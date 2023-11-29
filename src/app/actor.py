import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.app.interface import AbstractActor, ActorRegistry, IJournal
from src.domain.config import Settings
from src.domain.error import SystemNotSetError
from src.domain.interface import ActorRef, ICommand, IEntity, IEvent, IMessage
from src.domain.model import Command, Event
from src.infra.mq import MailBox


class EmptyEvents(Exception):
    ...


class Actor[TChild: "Actor[ty.Any]"](AbstractActor):
    mailbox: MailBox
    _system: ty.ClassVar["System[ty.Any]"]
    childs: ActorRegistry[ActorRef, TChild]

    def __init__(self, mailbox: MailBox):
        if not isinstance(self, System):
            self._ensure_system()

        self.childs = ActorRegistry()
        self.mailbox = mailbox
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
        if self.mailbox.size() == 0:
            return

        message = await self.mailbox.get()

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
        A non-recursive, non-none version of get_child
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


class StatefulActor[TChild: Actor[ty.Any], TState](Actor[TChild]):
    state: TState


class EntityActor[TChild: Actor[ty.Any], TEntity: IEntity](
    StatefulActor[TChild, TEntity]
):
    def __init__(self, mailbox: MailBox, entity: TEntity):
        super().__init__(mailbox=mailbox)
        self.entity = entity

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

    def __init__(self, mailbox: MailBox, settings: Settings):
        super().__init__(mailbox=mailbox)
        self.set_system(self)
        self._eventlog = EventLog(mailbox=MailBox.build())
        self._settings = settings
        self.__ref = settings.actor_refs.SYSTEM

    def ensure_self(self) -> None:
        """Pre start events"""
        ...

    def setup_eventlog(self, eventlog: ty.Optional["EventLog[ty.Any]"] = None) -> None:
        if eventlog is None:
            eventlog = EventLog(mailbox=MailBox.build())
        self._eventlog = eventlog

    @property
    def eventlog(self) -> "EventLog[TChild]":
        return self._eventlog

    def subscribe_events(self, actor: Actor[TChild]):
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
        return self.__ref


class EventLog[TListener: Actor[ty.Any]](Actor[ty.Any]):
    """
    a mediator that used to decouple event source(Actors) and event consumer (Journal)

    Actors.publish -> EventLog.receive -> Journal.receive

    coudld be refactor to a kafka publisher if needed
    """

    _event_listener: TListener

    def __init__(self, mailbox: MailBox):
        super().__init__(mailbox=mailbox)

    def register_listener(self, listener: TListener) -> None:
        self._event_listener = listener

    async def on_receive(self) -> None:
        msg = await self.mailbox.get()
        await self._event_listener.receive(msg)

    @property
    def event_listener(self) -> TListener:
        return self._event_listener

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @classmethod
    def build(cls) -> ty.Self:
        return cls(mailbox=MailBox.build())
