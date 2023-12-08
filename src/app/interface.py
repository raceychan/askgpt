import abc
import typing as ty
from functools import cached_property, singledispatchmethod

from src.domain.interface import ActorRef, ICommand, IEvent, IEventStore, IMessage


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


class AbstractActor(abc.ABC):
    @singledispatchmethod
    @abc.abstractmethod
    async def handle(self, command: ICommand) -> None:
        """
        Process/handle command, potentially change its state,
        *This should not return anything* to seperate command and query
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
