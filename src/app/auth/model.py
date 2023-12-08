import enum
import typing as ty
from datetime import datetime
from functools import singledispatchmethod

from pydantic import field_serializer

from src.app.model import UserInfo
from src.domain.interface import IRepository
from src.domain.model import Command, Entity, Event, Field, ValueObject, uuid_factory


class UserLoggedIn(Event):
    user_id: str
    last_login: datetime


class UserDeactivated(Event):
    user_id: str
    is_active: bool


class UserPromotedAdmin(Event):
    user_id: str
    is_admin: bool


class UserRoles(enum.StrEnum):
    # TODO: create corresponding privilages
    admin = enum.auto()
    user = enum.auto()


class AccessToken(ValueObject):
    ttl_m: int
    user_id: str
    role: str


class UserSignedUp(Event):
    entity_id: str = Field(alias="user_id")
    last_login: datetime
    user_info: UserInfo

    @field_serializer("last_login")
    def serialize_last_login(self, last_login: datetime) -> str:
        return last_login.isoformat()


class UserAuth(Entity):
    entity_id: str = Field(default_factory=uuid_factory, alias="user_id")
    role: UserRoles = UserRoles.user
    user_info: UserInfo
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
        self.last_login = datetime.utcnow()

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
            user_info=event.user_info,
            last_login=event.last_login,
        )


class IUserRepository(IRepository[UserAuth]):
    async def add(self, entity: UserAuth) -> None:
        ...

    async def update(self, entity: UserAuth) -> None:
        ...

    async def get(self, entity_id: str) -> UserAuth | None:
        ...

    async def remove(self, entity_id: str) -> None:
        ...

    async def list_all(self) -> list[UserAuth]:
        ...

    async def search_user_by_email(self, useremail: str) -> UserAuth | None:
        ...
