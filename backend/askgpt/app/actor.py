import abc
import asyncio
import typing as ty
from collections import deque
from functools import cached_property, singledispatchmethod

from askgpt.app.interface import AbstractActor, AbstractStetefulActor
from askgpt.domain.errors import GeneralAPPError, SystemNotSetError
from askgpt.domain.interface import (
    ActorRef,
    ICommand,
    IEntity,
    IEvent,
    IMessage,
    ISystem,
)
from askgpt.domain.model.base import Command, Event


class EmptyEvents(GeneralAPPError): ...


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
    # subclass should define __slots__ for memory efficiency

    @abc.abstractmethod
    def __len__(self) -> int: ...

    @abc.abstractmethod
    async def put(self, message: IMessage) -> None: ...

    @abc.abstractmethod
    async def get(self) -> IMessage | None: ...

    async def __aiter__(self) -> ty.AsyncGenerator[IMessage, ty.Any]:
        while msg := await self.get():
            yield msg

    def __bool__(self) -> bool:
        return self.__len__() > 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(capacity={self.capacity})"

    @property
    def capacity(self) -> int: ...

    def size(self) -> int: ...


class QueueBox(MailBox):
    __slots__ = ("_queue",)

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
    _system: ty.ClassVar["ISystem"]

    def __init__(self, boxfactory: BoxFactory) -> None:
        # if not isinstance(self, System):
        #     self._ensure_system()

        self.boxfactory = boxfactory
        self.mailbox = self.boxfactory()
        self.childs: ActorRegistry[ActorRef, TChild] = ActorRegistry()
        self._handle_sem = asyncio.Semaphore(1)

    def _ensure_system(self) -> None:
        if not hasattr(self, "system"):
            raise SystemNotSetError("Actor must be created under System")

        self.system.ensure_self()

    @property
    def system(self) -> "ISystem":
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
        else:
            raise TypeError("Unknown message type")

    async def publish(self, event: IEvent) -> None:
        await self.system.publish(event)

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
    def set_system(cls, system: ty.Any) -> None:
        sys_ = getattr(Actor, "_system", None)

        if sys_ is None:
            Actor._system = system
        elif sys_ is not system:
            raise Exception("Call set_system twice while system is already set")

    @cached_property
    def ref(self) -> ActorRef:
        return self.__class__.__name__.lower()


class StatefulActor[TChild: Actor[ty.Any], TState: ty.Any](
    AbstractStetefulActor, Actor[TChild]
):
    state: TState

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

    def rebuild(self, events: list[IEvent]) -> ty.Self:
        if not events:
            raise EmptyEvents(f"No events to rebuild {self.__class__.__name__}")

        for e in events:
            self.apply(e)

        return self


class EntityActor[TChild: Actor[ty.Any], TEntity: IEntity](Actor[TChild]):
    def __init__(
        self,
        entity: TEntity,
        boxfactory: BoxFactory,
    ):
        super().__init__(boxfactory=boxfactory)
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


# class System[TChild: Actor[ty.Any]](Actor[TChild]):
#     """
#     Singleton, should not be used directly, subclass it instead
#     """

#     def __new__(cls, *args: ty.Any, **kwargs: ty.Any):
#         if not hasattr(cls, "_system"):
#             cls._system = super().__new__(cls)
#         return cls._system

#     def __init__(
#         self,
#         ref: ActorRef,
#         settings: Settings,
#         producer: MessageProducer,
#         boxfactory: BoxFactory,
#     ):
#         super().__init__(boxfactory=boxfactory)
#         self.set_system(self)
#         self._producer = producer
#         self._settings = settings
#         self._ref = ref

#     def ensure_self(self) -> None:
#         """Pre start events"""
#         ...

#     @property
#     def settings(self) -> Settings:
#         return self._settings

#     @settings.setter
#     def settings(self, value: Settings) -> None:
#         self._settings = value

#     @cached_property
#     def ref(self) -> ActorRef:
#         return self._ref

#     async def start(self) -> None: ...
