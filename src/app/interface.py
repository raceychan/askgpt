import abc
import typing as ty
from functools import singledispatchmethod

from src.domain.interface import ICommand, IEvent, IMessage

# SubCommand = ty.TypeVar("SubCommand", bound=ICommand)


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

    # NOTE: this is just wrong, generic is not gonna save this
    # when override parent method, we only gonna make argument more general, return type more specific
    async def create_child(self, command: ICommand) -> ty.Self:
        raise NotImplementedError

    # TODO: this should be generic
    @abc.abstractmethod
    def get_child(self, entity_id: str) -> ty.Self | None:
        raise NotImplementedError

    def reply(self, message: IMessage) -> None:
        """
        sth like:
        self.send(message, message.sender)
        """
        raise NotImplementedError


class AbstractRef(ty.Protocol):
    ...


ActorRef = ty.Annotated[str, AbstractRef, "ActorRef"]

T = ty.TypeVar("T")
TRef = ty.TypeVar("TRef", bound="ActorRef")
TActor = ty.TypeVar("TActor", bound="AbstractActor")


# TODO:
class ActorRegistry(ty.Generic[TRef, TActor]):
    def __init__(self) -> None:
        self._dict: dict[TRef, TActor] = dict()

    def __getitem__(self, key: TRef) -> TActor:
        return self._dict[key]

    def __contains__(self, key: TRef) -> bool:
        return key in self._dict

    def __setitem__(self, key: TRef, value: TActor) -> None:
        self._dict[key] = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._dict})"

    def values(self) -> list[TActor]:
        return list(self._dict.values())

    def get(self, key: TRef, default: T) -> TActor | T:
        return self._dict.get(key, default)
