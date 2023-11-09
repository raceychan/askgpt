import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain import Command, Event, ISettings, SystemNotSetError
from src.infra import MailBox

from .interface import (
    AbstractActor,
    ActorRef,
    ActorRegistry,
    ICommand,
    IEvent,
    IMessage,
    TEntity,
    TState,
)


class Actor(AbstractActor):
    mailbox: MailBox
    _system: ty.ClassVar["System"]
    childs: ActorRegistry[ActorRef, "Actor"]

    def __init__(self, mailbox: MailBox):
        if not isinstance(self, System):
            self._ensure_system()

        self.childs = ActorRegistry()
        self.mailbox = mailbox
        self._handle_sem = asyncio.Semaphore(1)

    def _ensure_system(self) -> None:
        if not hasattr(self, "system"):
            raise SystemNotSetError("Actor must be created under System")

    @property
    def system(self) -> "System":
        return self._system

    async def send(self, message: IMessage, other: "Actor") -> None:
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

    def get_child(self, ref: ActorRef) -> ty.Optional["Actor"]:
        """
        Search for child actor recursively
        """
        if not self.childs:
            return None

        if actor := self.childs.get(ref):
            return actor

        for child_actor in self.childs.values():
            # if isinstance(child_actor, Supervisor):
            actor = child_actor.get_child(ref)
            if actor is None:
                continue
            return actor

        return None

    @singledispatchmethod
    async def handle(self, command: ICommand) -> None:
        raise NotImplementedError

    @classmethod
    def set_system(cls, system: "System") -> None:
        sys_ = getattr(Actor, "_system", None)

        if sys_ is None:
            Actor._system = system
        elif sys_ is not system:
            raise Exception("Call set_system twice while system is already set")

    @classmethod
    def rebuild(cls, events: list[Event]) -> ty.Self:
        if not events:
            raise Exception("No events to rebuild")
        created_event = events.pop(0)
        self = cls.apply(created_event)
        for e in events:
            self.apply(e)
        return self

    @cached_property
    def ref(self) -> ActorRef:
        return self.__class__.__name__.lower()


class StatefulActor(Actor, ty.Generic[TState]):
    ...


class EntityActor(StatefulActor[TEntity]):
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


# TChild = ty.TypeVar("TChild", bound="Actor")


# class Supervisor(Actor):

#     childs: ActorRegistry[ActorRef, Actor]

#     def __init__(self, mailbox: MailBox):
#         super().__init__(mailbox=mailbox)
#         self.childs = ActorRegistry()


#     def get_child(self, ref: ActorRef) -> ty.Optional["Actor"]:
#         """
#         Search for child actor recursively
#         """
#         if not self.childs:
#             return None

#         if actor := self.childs.get(ref):
#             return actor

#         for child_actor in self.childs.values():
#             #if isinstance(child_actor, Supervisor):
#             actor = child_actor.get_child(ref)
#             if actor is None:
#                 continue
#             return actor

# if (actor := child_actor.childs.get(ref)) is None:
#    continue
# return actor


class System(Actor):
    def __new__(cls, *args: ty.Any, **kwargs: ty.Any) -> "System":
        if not hasattr(cls, "_system"):
            cls._system = super().__new__(cls)
        return cls._system

    def __init__(self, mailbox: MailBox, settings: ISettings):
        super().__init__(mailbox=mailbox)
        self.set_system(self)
        self._settings = settings
        self.__eventlog_ref = settings.actor_refs.EVENTLOG
        self.__ref = settings.actor_refs.SYSTEM

    def create_eventlog(self, eventlog: ty.Optional["EventLog"] = None) -> None:
        if eventlog is None:
            eventlog = EventLog(mailbox=MailBox.build())
        self.childs[self.__eventlog_ref] = eventlog

    @property
    def eventlog(self) -> "EventLog":
        # Maybe we should just set this as an attribute?
        # type hint for this is quite difficult
        return self.childs[self.__eventlog_ref]

    @property
    def journal(self) -> "Actor":
        raise NotImplementedError

    @property
    def settings(self) -> ISettings:
        return self._settings

    @settings.setter
    def settings(self, value: ISettings) -> None:
        self._settings = value

    @cached_property
    def ref(self) -> ActorRef:
        return self.__ref


class EventLog(Actor):
    _event_listener: Actor

    def __init__(self, mailbox: MailBox):
        super().__init__(mailbox=mailbox)

    def register_listener(self, listener: Actor) -> None:
        self._event_listener = listener

    async def on_receive(self) -> None:
        msg = await self.mailbox.get()
        await self._event_listener.receive(msg)

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @classmethod
    def build(cls) -> ty.Self:
        return cls(mailbox=MailBox.build())
