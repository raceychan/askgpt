import abc
import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain.interface import ICommand, IEvent, IMessage, ISettings
from src.domain.model import Command, Entity, Event
from src.infra import MailBox

from .interface import AbstractActor, ActorRef, ActorRegistry


class SystemNotSetError(Exception):
    ...


# TODO: make this a generic type


# TODO: make this Generic of Command
# make commmand that belongs to certain actor all subcommand of that actor
# and make that actor a generic of Command

TEntity = ty.TypeVar("TEntity", bound=Entity)


class Actor(AbstractActor):
    entity: Entity  # TODO: Actor is a generic of Entity Generic[TEntity]
    mailbox: MailBox
    childs: ActorRegistry[ActorRef, ty.Self]
    _system: ty.ClassVar["System"]

    def __init__(self, mailbox: MailBox):
        self.childs = ActorRegistry()
        self.mailbox = mailbox
        if not isinstance(self, System):
            self._ensure_system()

        self._handle_sem = asyncio.Semaphore(1)

    def _ensure_system(self) -> None:
        if not hasattr(self, "system"):
            raise SystemNotSetError("Actor must be created under System")

    @property
    def system(self) -> "System":
        return self._system

    @cached_property
    def persistence_id(self) -> str:
        return f"{type(self).__name__}:{self.entity.entity_id}"

    def get_actor(self, actor_ref: ActorRef) -> ty.Optional["Actor"]:
        """
        recursive search for child actor
        """
        if (actor := self.get_child(actor_ref)) is not None:
            return actor

        for child in self.childs.values():
            actor = child.get_actor(actor_ref)
            if actor is None:
                continue
            return actor

        return None

    # TODO: this should be generic
    def get_child(self, entity_id: str) -> ty.Self | None:
        return self.childs.get(entity_id, None)

    # TODO: this should be generic
    async def get_or_create(self, command: ICommand) -> "Actor":
        actor = self.get_child(command.entity_id)
        if not actor:
            actor = await self.create_child(command)
        return actor

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

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @property
    def entity_id(self) -> str:
        return self.entity.entity_id

    @classmethod
    def set_system(cls, system: "System") -> None:
        sys_ = getattr(Actor, "_system", None)

        if sys_ is None:
            Actor._system = system
        elif sys_ is not system:
            raise Exception("Call set_system twice while system is already set")


from src.domain.interface import EventLogRef, JournalRef, SystemRef

SystemActorRefs = ty.TypeVar("SystemActorRefs", EventLogRef, JournalRef, SystemRef)
SystemActors = ty.TypeVar("SystemActors", bound=Actor)


class System(Actor):
    childs: dict[str, Actor]

    def __new__(cls, *args: ty.Any, **kwargs: ty.Any) -> "System":
        if not hasattr(cls, "_system"):
            cls._system = super().__new__(cls)
        return cls._system

    def __init__(self, mailbox: MailBox, settings: ISettings):
        super().__init__(mailbox=mailbox)
        self.set_system(self)
        self._settings = settings
        self.__eventlog_ref = settings.actor_refs.EVENTLOG

    def create_eventlog(self, eventlog: ty.Optional["EventLog"] = None) -> None:
        if eventlog is None:
            eventlog = EventLog(mailbox=MailBox.build())
        self.childs[self.__eventlog_ref] = eventlog

    @property
    def eventlog(self) -> "EventLog":
        return self.childs[self.__eventlog_ref]  # type: ignore

    @abc.abstractproperty
    def journal(self) -> "Actor":  # This should be generic, return childs["journal"]
        raise NotImplementedError

    @property
    def settings(self) -> ISettings:
        return self._settings

    @settings.setter
    def settings(self, value: ISettings) -> None:
        self._settings = value

    # def create_mediator(self, broker: MessageBroker | None = None):
    #     raise NotImplementedError


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


# class Mediator(Actor):
#     """
#     In-memory mediator
#     """

#     def __init__(self, mailbox: MailBox):
#         super().__init__(mailbox=mailbox)

#     async def handle(self, command: Command):
#         await self.system.handle(command)

#     def apply(self, event: Event):
#         raise NotImplementedError

#     @classmethod
#     def build(cls):
#         return cls(mailbox=MailBox.build())
