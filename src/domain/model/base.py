import abc
import datetime
import typing as ty
import uuid
from dataclasses import dataclass
from enum import Enum
from functools import singledispatchmethod

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, computed_field
from src.domain.model.name_tools import pascal_to_snake, str_to_snake

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


def enum_generator(
    **kwargs: dict[str, ty.Iterable[str]]
) -> ty.Generator["Enum", None, None]:
    """
    Example:
    -----
    >>> enum_gen = enum_generator(Color=["red", "green", "blue"])
    Color = next(enum_gen)
    assert issubclass(Color, Enum)
    assert isinstance(Color.red, Color)
    assert Color.red.value == "red"
    """

    for name, values in kwargs.items():
        yield Enum(name, {str_to_snake(v): v for v in values})


class DomainBase(BaseModel):
    "Base Model for domain objects, provide helper methods for serialization"

    model_config = ConfigDict(populate_by_name=True)

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

    def __str__(self):
        return self.__repr__()


class ValueObject(DomainBase):
    model_config = ConfigDict(frozen=True)


class Message(DomainBase):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    entity_id: str


class Command(Message):
    ...


class Query(Message):
    ...


class Event(Message):
    event_registry: ty.ClassVar[dict] = dict()

    entity_id: str
    version: ty.ClassVar[str] = "1.0.0"
    timestamp: utc_datetime = Field(default_factory=timestamp_factory)
    event_id: str = Field(default_factory=uuid_factory, alias="id")

    def __init_subclass__(cls, **kwargs):
        cls_id = f"{pascal_to_snake(cls.__name__)}"
        cls.event_registry[cls_id] = cls

    @classmethod
    def match_event_type(cls, event_type: str) -> "type[Event]":
        """
        Current implementation only works when event_type is globally unique
        for more complex application, we might need to consider using event_type of format
        <module>.<entity>.<event_type>
        or even
        <source>.<module>.<entity>.<event_type>
        askgpt.user_service.user.user_created

        then when parse
        1. assert source == project_name
        2. import module
        3. getattr(module, entity)
        4. getattr(entity, user_created)

        """
        return cls.event_registry[event_type]

    @classmethod
    def rebuild(cls, event_data: ty.Mapping):
        event_type = cls.match_event_type(event_data["event_type"])
        event = event_type(**event_data)
        return event

    @computed_field
    def event_type(self) -> str:
        return pascal_to_snake(self.__class__.__name__)


class Envelope(DomainBase):
    """
    Provide Meta data for event before sent to MQ,
    including data format, schema, etc.
    reff:
        1. https://developer.confluent.io/patterns/event/event-envelope/
        2. https://codeopinion.com/identify-commands-events/
    """

    headers: dict
    event: SerializeAsAny[Message] = Field(alias="payload")

    @classmethod
    def from_message(cls, message: Message) -> "Envelope":
        if isinstance(message, Event):
            return cls(payload=message, headers=dict())

        raise NotImplementedError


class EntityABC(abc.ABC):
    def predict_command(self, command: Command) -> Event:
        raise NotImplementedError

    @singledispatchmethod
    def apply(cls, event: Event):
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
