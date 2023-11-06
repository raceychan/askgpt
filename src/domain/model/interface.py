import typing as ty


class Identifiable(ty.Protocol):
    entity_id: str


class IEntity(Identifiable, ty.Protocol):
    ...


class IMessage(Identifiable, ty.Protocol):
    ...


class ICommand(IMessage, ty.Protocol):
    ...


class IEvent(IMessage, ty.Protocol):
    ...


class IQuery(IMessage, ty.Protocol):
    entity_id: str
