import abc
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain.model import Command, Entity, Event, Message
from src.infra.mq import MailBox


class AbstractRef:
    ...


ActorRef = ty.Annotated[str, AbstractRef, "ActorRef"]


class AbstractActor(abc.ABC):
    @abc.abstractmethod
    async def handle(self, command: Command) -> Event:
        "Process message"

    async def reply(self):
        raise NotImplementedError

    def create(self, aggregate_id: str) -> "Actor":
        "Create new actor"
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError


class Actor(AbstractActor):
    entity: Entity
    mailbox: MailBox
    childs: dict[str, "Actor"]

    def __init__(self, mailbox: MailBox):
        self.childs = dict()
        self.mailbox = mailbox

    @cached_property
    def persistence_id(self) -> str:
        return f"{type(self).__name__}:{self.entity.entity_id}"

    def get_child(self, aggregate_id: str) -> "Actor":
        child = self.childs.get(aggregate_id, None)
        # if not child:
        #     child = self.create(aggregate_id)
        #     self.childs[aggregate_id] = child
        return child

    async def send(self, message: Message, other: "Actor"):
        "Send message to other actor, message may contain information about sender id"
        await other.receive(message)

    async def receive(self, message: Message):
        "Receive message from other actor, may either persist or handle message or both"
        if isinstance(message, Command):
            await self.handle(message)
        elif isinstance(message, Event):
            self.apply(message)
        else:
            raise NotImplementedError

    def publish(self, event: Event):
        self.mailbox.put(event)

    def apply(self, event: Event):
        self.entity.apply(event)

    @singledispatchmethod
    async def handle(self, command: Command):
        actor = self.get_actor(command.entity_id)
        if actor is not None:
            await actor.handle(command)
        else:
            raise Exception("command not handled")

    def get_actor(self, actor_ref: ActorRef) -> "Actor":
        if not self.childs:
            raise Exception

        if (actor := self.get_child(actor_ref)) is not None:
            return actor

        for child in self.childs.values():
            actor = child.get_actor(actor_ref)
            if actor is None:
                continue
            return actor


class System(Actor):
    ...


class UnRegisteredCommandError(Exception):
    ...


class Mediator(Actor):
    """
    In-memory mediator
    """

    def __init__(self, mailbox: MailBox):
        self.mailbox = mailbox

    async def dispatch(self, command: Command):
        actor = self.get_child(command.entity_id)
        if actor:
            await actor.handle(command)

    # _dispatcher: dict[type[Command], Actor] = dict()

    # @classmethod
    # def register(cls, command: type[Command], actor: Actor):
    #     cls._dispatcher[command] = actor

    # def dispatch(self, command: Command) -> Actor:
    #     try:
    #         return self._dispatcher[command.__class__]
    #     except KeyError:
    #         raise UnRegisteredCommandError

    # async def send(self, command: Command):
    #     await self.dispatch(command).handle(command)

    # async def start(self):
    #     ...


# class System(Actor):
#     childs: dict[ActorRef, UserActor]

#     def __init__(self):
#         super().__init__(mailbox=MailBox.build())

#     def create_user(self, event: UserCreated) -> UserActor:
#         user_actor = UserActor.from_event(event)
#         self.childs[user_actor.entity.entity_id] = user_actor
#         self.publish(event)
#         return user_actor

#     def get_user(self, user_id: ActorRef):
#         if (user_actor := self.childs.get(user_id, None)) is None:
#             event = UserCreated(user_id=user_id)
#             user_actor = self.create_user(event)
#         return user_actor

#     def handle(self, command: Command):
#         if type(command) is CreateUser:
#             event = UserCreated(user_id=command.entity_id)
#             self.create_user(event)


# def setup_system(settings: Settings):
#     system = System()
#     journal
#     return system
