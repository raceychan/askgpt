import typing as ty
from collections import defaultdict
from functools import singledispatchmethod

from src.app.auth.model import UserAPIKeyAdded, UserSignedUp
from src.app.gpt.params import ChatGPTRoles, CompletionModels
from src.domain.interface import ICommand, IRepository
from src.domain.model.base import (
    Command,
    Entity,
    Event,
    Field,
    ValueObject,
    computed_field,
)
from src.domain.model.base import uuid_factory as uuid_factory
from src.domain.model.user import CreateUser, UserCreated


class ChatMessage(ValueObject):
    role: ChatGPTRoles
    content: str

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
    def as_user(cls, content: str) -> ty.Self:
        return cls(role="user", content=content)

    @classmethod
    def as_assistant(cls, content: str) -> ty.Self:
        return cls(role="assistant", content=content)

    @classmethod
    def as_prompt(cls, content: str) -> ty.Self:
        return cls(role="system", content=content)


class CreateSession(Command):
    user_id: str
    entity_id: str = Field(alias="session_id")


class SessionCreated(Event):
    session_id: str
    entity_id: str = Field(alias="user_id")


class SendChatMessage(Command):
    """
    TODO:
    refactor,
    class SendChatMessage(Command):
        client_type: str # openai, llama2 etc.
        chat_message: ChatMessage
    """

    message_body: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True
    entity_id: str = Field(alias="session_id")
    user_id: str
    role: ChatGPTRoles
    client_type: str = "openai"

    @computed_field  # type: ignore
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(role=self.role, content=self.message_body)


class ChatMessageSent(Event):
    entity_id: str = Field(alias="session_id")
    chat_message: ChatMessage


class ChatResponseReceived(ChatMessageSent):
    ...


# ================== Entities =====================


class ChatSession(Entity):
    entity_id: str = Field(alias="session_id")
    user_id: str
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

    def change_prompt(self, prompt: str) -> None:
        self.prompt = ChatMessage(role="system", content=prompt)

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


class User(Entity):
    entity_id: str = Field(alias="user_id")
    session_ids: list[str] = Field(default_factory=list)
    api_keys: dict[str, list[str]] = Field(default_factory=lambda: defaultdict(list))

    def predict_command(self, command: ICommand) -> list[SessionCreated]:
        if isinstance(command, CreateSession):
            return [
                SessionCreated(session_id=command.entity_id, user_id=self.entity_id)
            ]
        else:
            raise NotImplementedError

    @singledispatchmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register(UserCreated)
    @apply.register(UserSignedUp)
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
    async def add(self, entity: ChatSession) -> None:
        ...

    async def update(self, entity: ChatSession) -> None:
        ...

    async def get(self, entity_id: str) -> ChatSession | None:
        ...

    async def remove(self, entity_id: str) -> None:
        ...

    async def list_all(self) -> list[ChatSession]:
        ...
