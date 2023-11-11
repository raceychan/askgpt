import typing as ty
from functools import singledispatchmethod

from src.app.gpt.params import ChatGPTRoles, CompletionModels
from src.domain.model import (
    Command,
    Entity,
    Event,
    Field,
    ValueObject,
    computed_field,
    uuid_factory,
)


class TestDefaults:
    SYSTEM_ID: str = "system"
    USER_ID: str = "admin"
    SESSION_ID: str = "default_session"
    MODEL: CompletionModels = "gpt-3.5-turbo"


class ChatMessage(ValueObject):
    role: ty.Literal["system", "user", "assistant", "functio"]
    content: str
    # user_id: str

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
    user_id: str
    entity_id: str = Field(alias="session_id")


class UserAddedSession(Event):
    entity_id: str = Field(alias="user_id")
    session_id: str


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")


class SendChatMessage(Command):
    message_body: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True
    entity_id: str = Field(alias="session_id")
    user_id: str
    role: ChatGPTRoles

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
    entity_id: str = Field(alias="session_id", default_factory=uuid_factory)
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
        return cls(session_id=event.entity_id, user_id=event.user_id)

    @apply.register
    def _(self, event: ChatMessageSent) -> ty.Self:
        self.add_message(event.chat_message)
        return self

    @apply.register
    def _(self, event: ChatResponseReceived) -> ty.Self:
        self.add_message(event.chat_message)
        return self


# aggregate_root
class User(Entity):
    entity_id: str = Field(alias="user_id")
    # should hold session ids
    chat_sessions: dict[str, ChatSession] = Field(default_factory=dict)

    def add_session(self, session: ChatSession) -> None:
        self.chat_sessions[session.entity_id] = session

    def create_session(self, session_id: str) -> None:
        self.chat_sessions[session_id] = ChatSession(
            user_id=self.entity_id, session_id=session_id
        )

    def get_session(self, session_id: str) -> ChatSession | None:
        return self.chat_sessions.get(session_id)

    def list_sessions(self) -> tuple[ChatSession, ...]:
        return tuple(self.chat_sessions.values())

    @singledispatchmethod
    def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: UserCreated) -> ty.Self:
        return cls(user_id=event.entity_id)

    @apply.register
    def _(self, event: SessionCreated) -> ty.Self:
        session = ChatSession.apply(event)
        self.add_session(session)
        return self

    @apply.register
    def _(self, event: UserAddedSession) -> ty.Self:
        raise NotImplementedError
        return self

    @classmethod
    def create(cls, command: CreateUser) -> ty.Self:
        evt = UserCreated(user_id=command.entity_id)
        return cls.apply(evt)
