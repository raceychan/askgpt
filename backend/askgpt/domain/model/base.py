import abc
import datetime
import typing as ty
import uuid
from dataclasses import dataclass
from functools import singledispatchmethod

import orjson
import sqlalchemy as sa
from pydantic import AwareDatetime
from pydantic import BaseModel as BaseModel
from pydantic import ConfigDict as ConfigDict
from pydantic import EmailStr as EmailStr
from pydantic import Field as Field
from pydantic import SerializeAsAny as SerializeAsAny
from pydantic import computed_field as computed_field
from pydantic import field_serializer as field_serializer

from askgpt.domain.model.interface import ICommand, IEvent
from askgpt.helpers.string import str_to_snake
from askgpt.helpers.time import utc_now as utc_now

# from pydantic import validator as validator


frozen = dataclass(frozen=True, slots=True, kw_only=True)


"""
TODO: replace pydantic with bao's Struct, 
as we do not need data validation in domain layer
"""


def uuid_factory() -> str:
    return str(uuid.uuid4())


def request_id_factory() -> bytes:
    return uuid_factory().encode()


def json_dumps(obj: ty.Any) -> str:

    return orjson.dumps(obj).decode()


def json_loads(obj: str):
    # TODO: let orjson dumps bytes
    """
    my_bytes_value = b'[{\'Date\': \'2016-05-21T21:35:40Z\', \'CreationDate\': \'2012-05-05\', \'LogoType\': \'png\', \'Ref\': 164611595, \'Classe\': [\'Email addresses\', \'Passwords\'],\'Link\':\'http://some_link.com\'}]'

    fix_bytes_value = my_bytes_value.replace(b"'", b'"')

    my_json = json.load(io.BytesIO(fix_bytes_value))
    """
    return orjson.loads(obj.encode())


# TODO: this should just be a dataclass
class DomainModel(BaseModel):
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
    ) -> dict[str, ty.Any]:
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
    ) -> str:
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
        field_map: dict[str, ty.Any] = dict()
        computed_fields = cls.model_computed_fields
        for fname, finfo in computed_fields.items():
            ppt = finfo.wrapped_property
            getter = ppt.fget if isinstance(ppt, property) else ppt.func
            ftype = getter.__annotations__["return"]
            if issubclass(ftype, DomainModel):
                field_map[fname] = ftype.model_all_fields()
            field_map[fname] = ftype

        for fname, finfo in cls.model_fields.items():
            ftype = finfo.annotation
            if ftype and issubclass(ftype, DomainModel):
                field_map[fname] = ftype.model_all_fields()

            field_map[fname] = finfo.annotation
        return field_map

    @classmethod
    def tableclause(cls, table_name: str = "") -> sa.TableClause:
        import decimal
        import uuid

        types_mapping: dict[type | None, ty.Any] = {
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

        tablename = table_name or str_to_snake(cls.__name__)

        return sa.table(
            tablename,
            *[
                sa.column(fieldname, types_mapping[filedtype])
                for fieldname, filedtype in cls.model_all_fields().items()
            ],
        )

    def __str__(self) -> str:
        return self.__repr__()


class ValueObject(DomainModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)


class Message(DomainModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    entity_id: str


class DataStruct(DomainModel):
    "Pure Data object, no logic, no behavior, use to reduce code repetition"


class Command(Message): ...


class Query(Message): ...


class Event(Message):
    _event_registry: ty.ClassVar[dict[str, type[ty.Self]]] = dict()
    version: ty.ClassVar[str] = "1.0.0"

    entity_id: str
    event_id: str = Field(default_factory=uuid_factory, alias="id")
    timestamp: AwareDatetime = Field(default_factory=utc_now)

    def __init_subclass__(cls, **kwargs: ty.Any):
        cls_id = f"{str_to_snake(cls.__name__)}"
        cls._event_registry[cls_id] = cls

    @classmethod
    def match_event_type(cls, event_type: str, version: str) -> type["Event"]:
        """
        Current implementation only works when event_type is globally unique
        for more complex application, we might need to consider using event_type of format
        <module>.<entity>.<event_type>
        or even
        <source>.<module>.<entity>.<event_type>
        eg:
        askgpt.user_service.user.user_created
        """
        # TODO: use version to differentiate event type
        return cls._event_registry[event_type]

    @classmethod
    def rebuild(cls, event_data: ty.Mapping[str, ty.Any]) -> "Event":
        event_type = cls.match_event_type(
            event_data["event_type"], event_data["version"]
        )
        event = event_type.model_validate(event_data)
        return event

    @computed_field
    @property
    def event_type(self) -> str:
        return str_to_snake(self.__class__.__name__)

    def model_dump(
        self,
        mode: str = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        data = super().model_dump(
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
        data.update(version=self.version)
        return data


class Envelope(DomainModel):
    """
    Provide Meta data for event before sent to MQ,
    including data format, schema, etc.
    reff:
        1. https://developer.confluent.io/patterns/event/event-envelope/
        2. https://codeopinion.com/identify-commands-events/
    """

    headers: dict[str, ty.Any]
    event: SerializeAsAny[Message] = Field(alias="payload")

    @classmethod
    def from_message(cls, message: Message) -> "Envelope":
        if isinstance(message, Event):
            return cls(payload=message, headers=dict())
        raise NotImplementedError


class EntityABC(abc.ABC):
    def predict_command(self, command: ICommand) -> ty.Sequence[IEvent]:
        raise NotImplementedError

    @singledispatchmethod
    @abc.abstractmethod
    def apply(cls, event: Event) -> ty.Self:
        raise NotImplementedError

    @singledispatchmethod
    @abc.abstractmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError


class Entity(DomainModel, EntityABC):
    """
    Base Model for domain entities,
    subclass could mark domain id as entity_id by setting alias=True in field
    >>> Example:
    --------
    class User(Entity):
        user_id: str = Field(alias="entity_id")

    Configs:
    --------
        * populate_by_name=True
    """

    entity_id: str
