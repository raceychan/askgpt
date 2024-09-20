import datetime
import typing as ty
from functools import singledispatchmethod

utc_datetime = ty.Annotated[datetime.datetime, "UTC_TimeStamp"]


class IDomainObject:
    ...


class Identifiable(ty.Protocol):
    entity_id: str


class IEntity(Identifiable, ty.Protocol):
    entity_id: str

    @singledispatchmethod
    def apply(self, event: "IEvent") -> ty.Self:
        ...


class IMessage(Identifiable, ty.Protocol):
    def asdict(
        self,
        mode: str = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, ty.Any]:
        ...


class ICommand(IMessage, ty.Protocol):
    ...


class IEvent(IMessage, ty.Protocol):
    event_id: str
    version: ty.ClassVar[str]
    timestamp: datetime.datetime

    @property
    def event_type(self) -> str:
        ...


class IQuery(IMessage, ty.Protocol):
    entity_id: str


