import typing as ty
from functools import singledispatchmethod


class Identifiable(ty.Protocol):
    entity_id: str


class IEntity(Identifiable, ty.Protocol):
    entity_id: str

    @singledispatchmethod
    def apply(self, event: "IEvent") -> ty.Self:
        ...


class IMessage(Identifiable, ty.Protocol):
    ...


class ICommand(IMessage, ty.Protocol):
    ...


class IEvent(IMessage, ty.Protocol):
    ...


class IQuery(IMessage, ty.Protocol):
    entity_id: str
