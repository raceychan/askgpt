import abc
import asyncio
import typing as ty
from collections import deque
from functools import cached_property, singledispatchmethod

from src.app.interface import AbstractActor, IJournal
from src.domain.config import Settings
from src.domain.error import SystemNotSetError
from src.domain.interface import (
    ActorRef,
    ICommand,
    IEntity,
    IEvent,
    IEventStore,
    IMessage,
)
from src.domain.model.base import Command, Event


class EmptyEvents(Exception):
    ...


class ActorRegistry[TRef: ActorRef, TActor: "AbstractActor"]:
    def __init__(self) -> None:
        self._dict: dict[TRef, TActor] = dict()

    def __getitem__(self, key: TRef) -> TActor:
        return self._dict[key]

    def __contains__(self, key: TRef) -> bool:
        return key in self._dict

    def __setitem__(self, key: TRef, value: TActor) -> None:
        self._dict[key] = value

    def __bool__(self) -> bool:
        return bool(self._dict)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._dict})"

    def keys(self):
        return self._dict.keys()

    def values(self) -> list[TActor]:
        return list(self._dict.values())

    def get[T](self, key: TRef, default: T | None = None) -> TActor | T | None:
        return self._dict.get(key, default)


class MailBox(abc.ABC):
    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    @abc.abstractmethod
    async def put(self, message: IMessage) -> None:
        ...

    @abc.abstractmethod
    async def get(self) -> IMessage | None:
        ...

    async def __aiter__(self) -> ty.AsyncGenerator[IMessage, ty.Any]:
        while msg := await self.get():
            yield msg

    def __bool__(self) -> bool:
        return self.__len__() > 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(capacity={self.capacity})"

    @property
    def capacity(self) -> int:
        ...

    def size(self) -> int:
        ...


class QueueBox(MailBox):
    def __init__(self, maxsize: int = 0):
        self._queue: deque[IMessage] = deque(maxlen=maxsize or None)

    def __len__(self) -> int:
        return len(self._queue)

    async def put(self, message: IMessage) -> None:
        self._queue.append(message)

    async def get(self) -> IMessage | None:
        return self._queue.popleft()


type BoxFactory = ty.Callable[..., MailBox]


class Actor[TChild: "Actor[ty.Any]"](AbstractActor):
    _system: ty.ClassVar["System[ty.Any]"]

    def __init__(self, boxfactory: BoxFactory) -> None:
        if not isinstance(self, System):
            self._ensure_system()

        self.boxfactory = boxfactory
        self.mailbox = self.boxfactory()
        self.childs: ActorRegistry[ActorRef, TChild] = ActorRegistry()
        self._handle_sem = asyncio.Semaphore(1)

    def _ensure_system(self) -> None:
        if not hasattr(self, "system"):
            raise SystemNotSetError("Actor must be created under System")

        self.system.ensure_self()

    @property
    def system(self) -> "System[TChild]":
        return self._system

    async def send(self, message: IMessage, other: "Actor[ty.Any]") -> None:
        "Send message to other actor, message may contain information about sender id"
        await other.receive(message)

    async def receive(self, message: IMessage) -> None:
        "Receive message from other actor, may either persist or handle message or both"
        await self.mailbox.put(message)

        async with self._handle_sem:
            await self.on_receive()

    async def on_receive(self) -> None:
        message = await self.mailbox.get()
        if message is None:
            raise Exception("Mailbox is empty")

        if isinstance(message, Command):
            await self.handle(message)
        elif isinstance(message, Event):
            self.apply(message)
        else:
            raise TypeError("Unknown message type")

    async def publish(self, event: IEvent) -> None:
        await self.system.eventlog.receive(event)

    def get_child(self, ref: ActorRef) -> TChild | None:
        """
        Search for child actor recursively
        system.get_child would perform a global search
        """
        if not self.childs:
            return None

        if actor := self.childs.get(ref):
            return actor

        for child_actor in self.childs.values():
            actor = child_actor.get_child(ref)
            if actor is None:
                continue
            return actor

        return None

    def select_child(self, ref: ActorRef) -> TChild:
        """
        A non-recursive, affirmative version of get_child
        """
        return self.childs[ref]

    @singledispatchmethod
    async def handle(self, command: ICommand) -> None:
        raise NotImplementedError

    @classmethod
    def set_system(cls, system: "System[TChild]") -> None:
        sys_ = getattr(Actor, "_system", None)

        if sys_ is None:
            Actor._system = system
        elif sys_ is not system:
            raise Exception("Call set_system twice while system is already set")

    def rebuild(self, events: list[IEvent]) -> ty.Self:
        if not events:
            raise EmptyEvents(f"No events to rebuild {self.__class__.__name__}")

        for e in events:
            self.apply(e)

        return self

    @cached_property
    def ref(self) -> ActorRef:
        return self.__class__.__name__.lower()


class StatefulActor[TChild: Actor[ty.Any], TState: ty.Any](Actor[TChild]):
    state: TState


class EntityActor[TChild: Actor[ty.Any], TEntity: IEntity](
    StatefulActor[TChild, TEntity]
):
    def __init__(
        self,
        entity: TEntity,
        boxfactory: BoxFactory,
    ):
        super().__init__(boxfactory=boxfactory)
        self.state = self.entity = entity

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        self.entity.apply(event)
        return self

    @property
    def entity_id(self) -> str:
        return self.entity.entity_id

    @cached_property
    def persistence_id(self) -> str:
        return f"{type(self).__name__}:{self.entity.entity_id}"

    @cached_property
    def ref(self) -> ActorRef:
        return self.entity_id


class System[TChild: Actor[ty.Any]](Actor[TChild]):
    """
    Singleton, should not be used directly, subclass it instead
    """

    _eventlog: "EventLog[ty.Any]"
    _journal: IJournal

    def __new__(cls, *args: ty.Any, **kwargs: ty.Any) -> "ty.Self":
        if not hasattr(cls, "_system"):
            cls._system = super().__new__(cls)
        return cls._system

    def __init__(
        self,
        ref: ActorRef,
        settings: Settings,
        boxfactory: BoxFactory,
    ):
        super().__init__(boxfactory=boxfactory)
        self.set_system(self)
        self._eventlog = EventLog(boxfactory=boxfactory)
        self._settings = settings
        self._ref = ref

    def ensure_self(self) -> None:
        """Pre start events"""
        ...

    @property
    def eventlog(self) -> "EventLog[ty.Any]":
        return self._eventlog

    def subscribe_events(self, actor: Actor[ty.Any]):
        self._eventlog.register_listener(actor)

    @property
    def journal(self) -> "IJournal":
        return self._journal

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, value: Settings) -> None:
        self._settings = value

    @cached_property
    def ref(self) -> ActorRef:
        return self._ref

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @classmethod
    def from_settings(cls, settings: Settings) -> "System[TChild]":
        return cls(
            boxfactory=QueueBox, ref=settings.actor_refs.SYSTEM, settings=settings
        )


class EventLog[TListener: Actor[ty.Any]](Actor[ty.Any]):
    """
    a mediator that used to decouple event source(Actors) and event consumer (Journal)
    Actors.publish -> EventLog.receive -> Journal.receive
    coudld be refactor to a kafka publisher if needed
    """

    def __init__(
        self,
        boxfactory: BoxFactory,
        broadcast: bool = False,
    ):
        super().__init__(boxfactory=boxfactory)
        self._event_listeners: list[TListener] = []
        self._broadcast = broadcast

    def register_listener(self, listener: TListener) -> None:
        self._event_listeners.append(listener)

    async def on_receive(self) -> None:
        msg = await self.mailbox.get()
        if not msg:
            raise Exception("Mailbox is empty")

        if self._broadcast:
            raise NotImplementedError

        try:
            listener = self._event_listeners[0]
        except IndexError:
            raise Exception("No event listener registered")
        else:
            await listener.receive(msg)

    @property
    def event_listeners(self) -> list[TListener]:
        return self._event_listeners[:]

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError


class Journal(Actor[ty.Any]):
    """
    Consumer that consumes events from event bus and persist them to event store
    """

    def __init__(
        self, eventstore: IEventStore, boxfactory: BoxFactory, ref: ActorRef
    ) -> None:
        super().__init__(boxfactory=boxfactory)
        self.system.subscribe_events(self)
        self.eventstore = eventstore
        self._ref = ref

    async def on_receive(self) -> None:
        message = await self.mailbox.get()
        if message is None:
            raise Exception("Mailbox is empty")

        if isinstance(message, Event):
            await self.eventstore.add(message)
        else:
            raise NotImplementedError("Currently journal only accepts events")

    @singledispatchmethod
    async def handle(self, message: IMessage) -> None:
        raise NotImplementedError

    async def persist_event(self) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        await self.persist_event()

    @singledispatchmethod
    def apply(self, event: IEvent) -> ty.Self:
        raise NotImplementedError

    async def publish(self, event: IEvent) -> None:
        await self.mailbox.put(event)
        await self.on_receive()

    @cached_property
    def ref(self) -> ActorRef:
        return self._ref

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        return await self.eventstore.get(entity_id=ref)
