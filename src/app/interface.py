import abc
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain.interface import ActorRef, ICommand, IEvent, IEventStore, IMessage


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

    @singledispatchmethod
    @abc.abstractmethod
    def apply(self, event: IEvent) -> ty.Self:
        raise NotImplementedError

    def reply(self, message: IMessage) -> None:
        """
        sth like:
        self.send(message, message.sender)
        """
        raise NotImplementedError


class IJournal(ty.Protocol):
    eventstore: IEventStore

    @cached_property
    def ref(self) -> ActorRef:
        ...

    async def list_events(self, ref: ActorRef) -> "list[IEvent]":
        ...
        # return await self.eventstore.get(entity_id=ref)
