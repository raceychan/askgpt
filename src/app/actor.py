import abc
import asyncio
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain.model import Command, Entity, Event, Message
from src.infra.mq import MailBox


class AbstractRef:
    ...


ActorRef = ty.Annotated[str, AbstractRef, "ActorRef"]


class AbstractActor(abc.ABC):
    def reply(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def handle(self, command: Command):
        """
        Process/handle command, potentially change its state,
        this should not return anything to seperate command and query
        """
        raise NotImplementedError

    @abc.abstractmethod
    def receive(self, message: Message):
        raise NotImplementedError

    @singledispatchmethod
    @abc.abstractmethod
    def apply(self, event: Event):
        raise NotImplementedError

    async def create_child(self, command: Command) -> "Actor":
        raise NotImplementedError

    def get_child(self, entity_id: str) -> "Actor":
        raise NotImplementedError


class Actor(AbstractActor):
    entity: Entity
    mailbox: MailBox
    childs: dict[str, "Actor"]
    _system: ty.ClassVar["System"]

    def __init__(self, mailbox: MailBox):
        self.childs = dict()
        self.mailbox = mailbox
        if not isinstance(self, System):
            self._ensure_system()

        self._handle_sem = asyncio.Semaphore(1)

    def _ensure_system(self):
        if not isinstance(self.system, System):
            raise Exception("Actor must be created under System")

    @property
    def system(self):
        return self._system

    @cached_property
    def persistence_id(self) -> str:
        return f"{type(self).__name__}:{self.entity.entity_id}"

    def get_actor(self, actor_ref: ActorRef) -> ty.Optional["Actor"]:
        if (actor := self.get_child(actor_ref)) is not None:
            return actor

        for child in self.childs.values():
            actor = child.get_actor(actor_ref)
            if actor is None:
                continue
            return actor

    def get_child(self, entity_id: str) -> ty.Optional["Actor"]:
        return self.childs.get(entity_id, None)

    async def get_or_create(self, command: Command) -> "Actor":
        actor = self.get_child(command.entity_id)
        if not actor:
            actor = await self.create_child(command)
        return actor

    async def send(self, message: Message, other: "Actor"):
        "Send message to other actor, message may contain information about sender id"
        await other.receive(message)

    async def receive(self, message: Message):
        "Receive message from other actor, may either persist or handle message or both"
        await self.mailbox.put(message)

        async with self._handle_sem:
            await self.on_receive()

    async def on_receive(self):
        if self.mailbox.size() == 0:
            return

        message = await self.mailbox.get()

        if isinstance(message, Command):
            await self.handle(message)
        elif isinstance(message, Event):
            self.apply(message)
        else:
            raise TypeError("Unknown message type")

    async def publish(self, event: Event):
        # TODO: rewrite this
        # create a queue actor, pass it to both system and journal
        # where all events send to Queue Actor
        # and Queue Actor forward them to journal

        journal = self.system.get_child("journal")
        if not journal:
            raise Exception("Journal not created")
        await journal.receive(event)

    @singledispatchmethod
    async def handle(self, command: Command):
        breakpoint()
        raise NotImplementedError

    @property
    def entity_id(self):
        return self.entity.entity_id

    @classmethod
    def set_system(cls, system: "System"):
        if (sys_ := getattr(Actor, "_system", None)) is not None:
            if sys_ is not system:
                raise Exception("System already set")
            return
        if not isinstance(system, System):
            raise Exception("System must be instance of System")
        Actor._system = system


class System(Actor):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_system"):
            cls._system = super().__new__(cls)
        return cls._system

    def __init__(self, mailbox: MailBox):
        super().__init__(mailbox=mailbox)
        self.set_system(self)
        self._journal_started_event = asyncio.Event()

    # @property
    # def journal(self) -> Journal:
    #     return self.system.childs["journal"]  # type: ignore


class Mediator(Actor):
    """
    In-memory mediator
    """

    def __init__(self, mailbox: MailBox):
        super().__init__(mailbox=mailbox)

    async def handle(self, command: Command):
        await self.system.handle(command)

    def apply(self, event: Event):
        raise NotImplementedError

    @classmethod
    def build(cls):
        return cls(mailbox=MailBox.build())
