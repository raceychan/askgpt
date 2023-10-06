import abc
import datetime
import typing as ty
import uuid
from dataclasses import dataclass
from functools import cached_property, singledispatchmethod

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, computed_field

from src.domain.model.name_tools import pascal_to_snake

utc_datetime = ty.Annotated[datetime.datetime, "UTC_TimeStamp"]

frozen = dataclass(frozen=True, slots=True, kw_only=True)


def rich_repr(namespace: ty.Mapping, indent="\t"):
    lines = ""
    for key, val in namespace.items():
        if not key.startswith("_"):
            if isinstance(val, dict):
                lines += f"{indent}{key}=\n" + rich_repr(val, indent + indent)
            elif hasattr(val, "__dict__"):
                lines += f"{indent}{key}=\n" + rich_repr(val.__dict__, indent + indent)
            else:
                lines += f"{indent}{key}={val}\n"
    return lines


def uuid_factory() -> str:
    return str(uuid.uuid4())


def timestamp_factory() -> utc_datetime:
    return datetime.datetime.utcnow()


class DomainBase(BaseModel):
    "Base Model for domain objects, provide helper methods for serialization"

    def asdict(
        self,
        mode: ty.Literal["json", "python"] | str = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        return self.model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def asjson(
        self,
        indent: int | None = None,
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        return self.model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    @classmethod
    def model_all_fields(cls) -> dict[str, type]:
        field_map = dict()
        computed_fields = cls.model_computed_fields.fget(cls)  # type: ignore
        for fname, finfo in computed_fields.items():
            ppt = finfo.wrapped_property
            getter = ppt.fget if isinstance(ppt, property) else ppt.func
            ftype = getter.__annotations__["return"]
            if issubclass(ftype, DomainBase):
                field_map[fname] = ftype.model_all_fields()
            field_map[fname] = ftype

        for fname, finfo in cls.model_fields.items():
            ftype = finfo.annotation
            if issubclass(ftype, DomainBase):  # type: ignore
                field_map[fname] = ftype.model_all_fields()

            field_map[fname] = finfo.annotation
        return field_map

    @classmethod
    def tableclause(cls, table_name: str = ""):
        import decimal
        import uuid

        import sqlalchemy as sa

        types_mapping = {
            str: sa.String,
            int: sa.Integer,
            datetime.datetime: sa.DateTime,
            bool: sa.Boolean,
            float: sa.Float,
            list: sa.JSON,
            dict: sa.JSON,
            uuid.UUID: sa.UUID,
            None: sa.Null,
            decimal.Decimal: sa.Numeric,
        }

        tablename = table_name or pascal_to_snake(cls.__name__)

        return sa.table(
            tablename,
            *[
                sa.column(fieldname, types_mapping[filedtype])
                for fieldname, filedtype in cls.model_all_fields().items()
            ],
        )


class ValueObject(DomainBase):
    model_config = ConfigDict(frozen=True)


class Message(DomainBase):
    # model_config = ConfigDict(frozen=True)
    model_config = ConfigDict(frozen=True, populate_by_name=True)


class Command(Message):
    ...


class Query(Message):
    ...


class Event(Message):
    version: ty.ClassVar[str] = "1.0.0"
    entity_id: str
    timestamp: utc_datetime = Field(default_factory=timestamp_factory)

    @computed_field
    @cached_property
    def event_id(self) -> str:
        return str(uuid.uuid4())

    @computed_field
    @cached_property
    def event_type(self) -> str:
        return pascal_to_snake(self.__class__.__name__)


class Envelope(DomainBase):
    "NOTE: shoud this contain both event and command?"
    event: SerializeAsAny[Event] = Field(alias="payload")

    @classmethod
    def from_event(cls, event: Event):
        return cls(payload=event)

    @computed_field
    @cached_property
    def event_id(self) -> str:
        return self.event.event_id

    @computed_field
    def event_type(self) -> str:
        return self.event.event_type

    @computed_field(alias="aggregate_id")
    def entity_id(self) -> str:
        return self.event.entity_id

    @computed_field
    def timestamp(self) -> datetime.datetime:
        return self.event.timestamp

    @computed_field
    def version(self) -> str:
        return self.event.version


class EntityABC(abc.ABC):
    def predict_command(self, command: Command) -> Event:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @abc.abstractmethod
    def _(self, event: Event):
        ...

    @abc.abstractmethod
    def handle(self, command: Command):
        raise NotImplementedError


class Entity(DomainBase, EntityABC):
    """
    Base Model for domain entities,
    subclass could mark domain id as entity_id by setting alias=True in field
    >>> Example:
    --------
    class User(Entity):
        usr_id: str = Field(alias="entity_id")

    Configs:
    --------
        * populate_by_name=True
    """

    entity_id: str
    model_config = ConfigDict(populate_by_name=True)
