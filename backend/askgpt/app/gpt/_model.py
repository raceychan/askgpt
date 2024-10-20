import typing as ty
from collections import defaultdict
from functools import singledispatchmethod

from askgpt.app.auth._model import UserAPIKeyAdded, UserSignedUp
from askgpt.domain.interface import ICommand, IRepository
from askgpt.domain.model.base import (
    Command,
    DataStruct,
    Entity,
    Event,
    Field,
    ValueObject,
    computed_field,
)
from askgpt.domain.model.base import uuid_factory as uuid_factory
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers.time import utc_now
from pydantic import AwareDatetime

from .openai._params import ChatGPTRoles, CompletionModels

DEFAULT_SESSION_NAME = "New Session"


class ChatMessage(ValueObject):
    role: ChatGPTRoles
    content: str
    gpt_type: SupportedGPTs
    timestamp: AwareDatetime = Field(default_factory=utc_now)

    @property
    def is_prompt(self) -> bool:
        return self.role == "system"

    @property
    def is_question(self) -> bool:
        return self.role == "user"

    @property
    def is_answer(self) -> bool:
        return self.role == "assistant"

    @classmethod
    def as_user(cls, content: str, gpt_type: SupportedGPTs) -> ty.Self:
        return cls(role="user", content=content, gpt_type=gpt_type)

    @classmethod
    def as_assistant(cls, content: str, gpt_type: SupportedGPTs) -> ty.Self:
        return cls(role="assistant", content=content, gpt_type=gpt_type)

    @classmethod
    def as_prompt(cls, content: str, gpt_type: SupportedGPTs) -> ty.Self:
        return cls(role="system", content=content, gpt_type=gpt_type)

    def asdict(self):  # type: ignore
        # TODO: find a better way to handle this
        # oepnai can't handle datetime objects in the messages
        d = self.model_dump(exclude={"user_id", "timestamp"})
        return d


class UserRelated(DataStruct):
    entity_id: str = Field(alias="user_id")


class SessionRelated(DataStruct):
    entity_id: str = Field(alias="session_id")


class CreateSession(SessionRelated, Command):
    user_id: str
    session_name: str = DEFAULT_SESSION_NAME
    session_id: str


class SessionCreated(UserRelated, Event):
    session_name: str = DEFAULT_SESSION_NAME
    session_id: str


class SessionRenamed(SessionRelated, Event):
    new_name: str


class SessionRemoved(SessionRelated, Event): ...


class SendChatMessage(SessionRelated, Command):
    message_body: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True
    user_id: str
    role: ChatGPTRoles
    gpt_type: SupportedGPTs

    @computed_field  # type: ignore
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(
            role=self.role, content=self.message_body, gpt_type=self.gpt_type
        )


class ChatMessageSent(SessionRelated, Event):
    chat_message: ChatMessage


class ChatResponseReceived(ChatMessageSent): ...


# ================== Entities =====================


class ChatSession(Entity):
    entity_id: str = Field(alias="session_id")
    user_id: str
    session_name: str = DEFAULT_SESSION_NAME
    messages: list[ChatMessage] = Field(default_factory=list)

    @property
    def prompt(self) -> ChatMessage | None:
        init_msg = self.messages[0]
        return init_msg if init_msg.is_prompt else None

    @prompt.setter
    def prompt(self, prompt: ChatMessage) -> None:
        if not prompt.is_prompt:
            raise Exception("prompt must be a system message")

        self.messages.insert(0, prompt)

    def add_message(self, chat_message: ChatMessage) -> None:
        self.messages.append(chat_message)

    def change_prompt(self, prompt: str, gpt_type: SupportedGPTs) -> None:
        self.prompt = ChatMessage(role="system", content=prompt, gpt_type=gpt_type)

    @singledispatchmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SessionCreated) -> ty.Self:
        return cls(session_id=event.session_id, user_id=event.entity_id)

    @apply.register
    def _(self, event: ChatMessageSent) -> ty.Self:
        self.add_message(event.chat_message)
        return self

    @apply.register
    def _(self, event: ChatResponseReceived) -> ty.Self:
        self.add_message(event.chat_message)
        return self

    @apply.register
    def _(self, event: SessionRenamed) -> ty.Self:
        self.session_name = event.new_name
        return self


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")


# TODO: move this to auth service
class User(Entity):
    entity_id: str = Field(alias="user_id")
    session_ids: list[str] = Field(default_factory=list)
    api_keys: dict[str, list[str]] = Field(
        default_factory=lambda: defaultdict[str, list[str]](list)
    )

    def predict_command(self, command: ICommand) -> list[SessionCreated]:
        if isinstance(command, CreateSession):
            return [
                SessionCreated(
                    session_id=command.entity_id,
                    user_id=self.entity_id,
                    session_name=command.session_name,
                )
            ]
        else:
            raise NotImplementedError

    @singledispatchmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: UserCreated | UserSignedUp) -> ty.Self:
        return cls(user_id=event.entity_id)

    @apply.register
    def _(self, event: SessionCreated) -> ty.Self:
        self.session_ids.append(event.session_id)
        return self

    @apply.register
    def _(self, event: UserAPIKeyAdded) -> ty.Self:
        self.api_keys[event.api_type].append(event.api_key)
        return self

    @classmethod
    def create(cls, command: CreateUser) -> ty.Self:
        evt = UserCreated(user_id=command.entity_id)
        return cls.apply(evt)

    def get_keys_of_type(self, api_type: str) -> list[str]:
        return self.api_keys.get(api_type, [])


class ISessionRepository(IRepository[ChatSession]):
    async def add(self, entity: ChatSession) -> None: ...

    async def update(self, entity: ChatSession) -> None: ...

    async def get(self, entity_id: str) -> ChatSession | None: ...

    async def remove(self, entity_id: str) -> None: ...

    async def list_all(self) -> list[ChatSession]: ...
