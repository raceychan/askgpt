import abc
from functools import cached_property

from src.domain.model import Command, Entity, Message, Query
from src.infra.mq import MailBox


class Actor(abc.ABC):
    aggregate: Entity
    mailbox: MailBox

    @cached_property
    def persistence_id(self) -> str:
        return f"{type(self).__name__}:{self.aggregate.entity_id}"

    @abc.abstractmethod
    def handle(self, message: Message):
        "Process message"

    def send(self, message: Message, other: "Actor"):
        "Send message to other actor, message may contain information about sender id"
        other.receive(message)

    def receive(self, message: Message):
        "Receive message from other actor, may either persist or handle message or both"
        self.handle(message)

    def reply(self):
        ...

    def create(self, aggregate_id: str) -> "Actor":
        "Create new actor"
        ...

    def save_event(self, event):
        ...

    def handle_command(self, command: Command):
        event = self.handle(command)
        self.save_event(event)


class Root(Actor):
    childs: dict[str, "Actor"]

    def __init__(self, aggrate: "Aggregate"):
        self.aggregate = aggrate
        self.childs = dict()

    def get_actor(self, aggregate_id: str) -> Actor:
        child = self.childs.get(aggregate_id)
        if not child:
            child = self.create(aggregate_id)
            self.childs[aggregate_id] = child
        return child