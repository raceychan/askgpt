import typing as ty
from functools import singledispatchmethod

from src.domain.model import (
    Command,
    Entity,
    Event,
    Field,
    Message,
    ValueObject,
    computed_field,
    uuid_factory,
)

# TODO: read
# https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/domain-events-design-implementation


# class ModelEndpoint(BaseModel):
#     endpoint: Path
#     models: tuple[str, ...]


# class CompletionEndPoint(ModelEndpoint):
#     endpoint: Path = Path("/v1/chat/completion")
#     model: CompletionModels


CompletionModels = ty.Literal[
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-16k-0613",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-32k",
    "gpt-4-32k-0613",
]


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
    def is_prompt(self):
        return self.role == "system"

    @property
    def is_question(self):
        return self.role == "user"

    @property
    def is_answer(self):
        return self.role == "assistant"

    @classmethod
    def as_user(cls, content: str):
        return cls(role="user", content=content)

    @classmethod
    def as_assistant(cls, content: str):
        return cls(role="assistant", content=content)

    @classmethod
    def as_prompt(cls, content: str):
        return cls(role="system", content=content)


# class UserChatMessage(ChatMessage):
#     role: ty.Literal["user"] = "user"
#     # user_id: str


# class AssistantChatMessage(ChatMessage):
#     role: ty.Literal["assistant"] = "assistant"


class CreateSession(Command):
    user_id: str
    entity_id: str = Field(alias="session_id")


class SessionCreated(Event):
    user_id: str
    entity_id: str = Field(alias="session_id")


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")


class SendChatMessage(Command):
    user_message: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True
    entity_id: str = Field(alias="session_id")
    user_id: str

    @computed_field
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(role="user", content=self.user_message)


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
    def prompt(self):
        init_msg = self.messages[0]
        return init_msg if init_msg.is_prompt else None

    @prompt.setter
    def prompt(self, prompt: ChatMessage):
        if not prompt.is_prompt:
            raise Exception("prompt must be a system message")

        self.messages.insert(0, prompt)

    def add_message(self, chat_message: ChatMessage):
        self.messages.append(chat_message)

    def change_prompt(self, prompt: str):
        self.prompt = ChatMessage(role="system", content=prompt)

    @singledispatchmethod
    def handle(self, command: Command):
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SessionCreated):
        return cls(session_id=event.entity_id, user_id=event.user_id)

    @apply.register
    def _(self, event: ChatMessageSent):
        self.add_message(event.chat_message)

    @apply.register
    def _(self, event: ChatResponseReceived):
        self.add_message(event.chat_message)


# aggregate_root
class User(Entity):
    entity_id: str = Field(alias="user_id")
    chat_sessions: dict[str, ChatSession] = Field(default_factory=dict)

    def add_session(self, session: ChatSession):
        self.chat_sessions[session.entity_id] = session

    def create_session(self, session_id: str):
        self.chat_sessions[session_id] = ChatSession(
            user_id=self.entity_id, session_id=session_id
        )

    def get_session(self, session_id: str):
        return self.chat_sessions.get(session_id)

    @singledispatchmethod
    def handle(self, message: Message):
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @handle.register
    @classmethod
    def _(cls, command: CreateUser):
        evt = UserCreated(user_id=command.entity_id)
        user = cls.apply(evt)
        return user

    @apply.register
    @classmethod
    def _(cls, event: UserCreated):
        return cls(user_id=event.entity_id)

    @apply.register
    def _(self, event: SessionCreated):
        session = ChatSession.apply(event)
        self.add_session(session)
