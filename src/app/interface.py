import abc
import typing as ty
from functools import singledispatchmethod

from src.domain.interface import ActorRef as ActorRef
from src.domain.interface import ICommand, IEvent
from src.domain.interface import IEventStore as IEventStore
from src.domain.interface import IMessage


class AbstractActor(abc.ABC):
    @singledispatchmethod
    @abc.abstractmethod
    async def handle(self, command: ICommand) -> None:
        """
        Process/handle command, potentially change its state,
        This should not return anything to seperate command and query
        """

        raise NotImplementedError

    @abc.abstractmethod
    async def receive(self, message: IMessage) -> None:
        raise NotImplementedError

    def reply(self, message: IMessage) -> None:
        """
        sth like:
        self.send(message, message.sender)
        """
        raise NotImplementedError


class AbstractStetefulActor(AbstractActor):
    @singledispatchmethod
    @abc.abstractmethod
    def apply(self, event: IEvent) -> ty.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def rebuild(self, events: "list[IEvent]") -> ty.Self:
        ...


class IJournal(ty.Protocol):
    eventstore: IEventStore

    def ref(self) -> ActorRef:
        ...

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        ...
