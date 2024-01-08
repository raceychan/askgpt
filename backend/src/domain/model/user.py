import typing as ty

from src.domain.model.base import (
    Command,
    EmailStr,
    Event,
    Field,
    ValueObject,
    field_serializer,
)
from src.infra import security


class UserInfo(ValueObject):
    version: ty.ClassVar[str] = "1.0.0"

    user_name: str = ""
    user_email: EmailStr
    hash_password: bytes

    @field_serializer("hash_password")
    def decode_password(self, hash_password: bytes) -> str:
        return hash_password.decode()

    def verify_password(self, password: str) -> bool:
        return security.verify_password(password.encode(), self.hash_password)


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")
    # user_info: UserInfo


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")
    # user_info: UserInfo
