import typing as ty

from src.domain import encrypt
from src.domain.model.base import (
    Command,
    EmailStr,
    Event,
    Field,
    ValueObject,
    field_serializer,
)


class UserInfo(ValueObject):
    version: ty.ClassVar[str] = "1.0.0"

    user_name: str | None = None
    user_email: EmailStr
    hash_password: bytes

    @field_serializer("hash_password")
    def serialize_password(self, hash_password: bytes) -> str:
        return hash_password.decode()

    def verify_password(self, password: str) -> bool:
        return encrypt.verify_password(password.encode(), self.hash_password)


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")
    user_info: UserInfo


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")
    user_info: UserInfo


class TestDefaults:
    SYSTEM_ID: str = "system"
    USER_ID: str = "5aba4f79-19f7-4bd2-92fe-f2cdb43635a3"
    USER_NAME: str = "admin"
    USER_EMAIL: str = "admin@gmail.com"
    USER_PASSWORD: str = "password"  # .encode()
    SESSION_ID: str = "e0b5ee4a-ef76-4ed9-89fb-5f7a64122dc8"
    SESSION_NAME: str = "default_session"
    MODEL: str = "gpt-3.5-turbo"
    USER_INFO: UserInfo = UserInfo(
        user_email=USER_EMAIL,
        user_name=USER_NAME,
        hash_password=encrypt.hash_password(USER_PASSWORD.encode()),
    )
