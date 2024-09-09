import enum
import typing as ty
from datetime import datetime
from functools import singledispatchmethod

from pydantic import field_serializer
from src.domain.interface import IRepository
from src.domain.model.base import (  # uuid_factory,
    Command,
    EmailStr,
    Entity,
    Event,
    Field,
    ValueObject,
    utcts_factory,
)
from src.infra import security


class UserCredential(ValueObject):
    version: ty.ClassVar[str] = "1.0.0"

    user_name: str = ""
    user_email: EmailStr
    hash_password: bytes

    @field_serializer("hash_password")
    def decode_password(self, hash_password: bytes) -> str:
        return hash_password.decode()

    def verify_password(self, password: str) -> bool:
        return security.verify_password(password.encode(), self.hash_password)

class UserLoggedIn(Event):
    entity_id: str = Field(alias="user_id")
    last_login: datetime


class UserDeactivated(Event):
    entity_id: str = Field(alias="user_id")
    is_active: bool = False


class UserPromotedAdmin(Event):
    entity_id: str = Field(alias="user_id")
    is_admin: bool


class UserRoles(enum.StrEnum):
    # TODO: create corresponding privilages
    admin = enum.auto()
    user = enum.auto()


class UserSignedUp(Event):
    entity_id: str = Field(alias="user_id")
    last_login: datetime
    credential: UserCredential

    @field_serializer("last_login")
    def serialize_last_login(self, last_login: datetime) -> str:
        return last_login.isoformat()


class UserAPIKeyAdded(Event):
    entity_id: str = Field(alias="user_id")
    api_key: str
    api_type: str


class UserAuth(Entity):
    entity_id: str = Field(alias="user_id")
    role: UserRoles = UserRoles.user
    credential: UserCredential
    last_login: datetime
    is_active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role == UserRoles.admin

    def promote_to_admin(self) -> None:
        self.role = UserRoles.admin

    def deactivate(self) -> None:
        self.is_active = False

    def login(self) -> None:
        self.last_login = utcts_factory()

    @singledispatchmethod
    def apply(cls, event: Event) -> ty.Self:
        raise NotImplementedError

    @singledispatchmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: UserSignedUp) -> ty.Self:
        return cls(
            user_id=event.entity_id,
            credential=event.credential,
            last_login=event.last_login,
        )

    @apply.register
    def _(self, event: UserDeactivated) -> ty.Self:
        self.deactivate()
        return self


class IUserRepository(IRepository[UserAuth]):
    async def add(self, entity: UserAuth) -> None: ...

    async def update(self, entity: UserAuth) -> None: ...

    async def get(self, entity_id: str) -> UserAuth | None: ...

    async def remove(self, entity_id: str) -> None: ...

    async def list_all(self) -> list[UserAuth]: ...

    async def search_user_by_email(self, useremail: str) -> UserAuth | None: ...


class AccessPayload(ValueObject):
    role: UserRoles


class AccessToken(security.JWTBase, AccessPayload): ...
