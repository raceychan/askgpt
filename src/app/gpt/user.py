import typing as ty

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


class ChatMessage(ValueObject):
    role: ty.Literal["system", "user", "assistant", "functio"]
    content: str


class CreateSession(Command):
    user_id: str
    session_id: str


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
    session_id: str

    @computed_field
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(role="user", content=self.user_message)


class ChatMessageSent(Event):
    session_id: str
    chat_message: ChatMessage


# ================== Entities =====================


class ChatSession(Entity):
    session_id: str = Field(alias="entity_id", default_factory=uuid_factory)
    user_id: str
    messages: list[ChatMessage] = Field(default_factory=list)

    def handle(self, command: Command):
        ...

    @Entity.apply.register
    @classmethod
    def _(cls, event: SessionCreated):
        return cls(entity_id=event.entity_id, user_id=event.user_id)


# aggregate_root
class User(Entity):
    entity_id: str = Field(alias="user_id")
    chat_sessions: dict[str, ChatSession] = Field(default_factory=dict)

    def add_new_session(self):
        new_session = ChatSession(user_id=self.user_id)  # type: ignore
        self.chat_sessions[new_session.session_id] = new_session

    def handle(self, message: Message):
        if type(message) == "AddNewSession":
            ...

    @Entity.apply.register
    @classmethod
    def _(cls, event: UserCreated):
        return cls(user_id=event.entity_id)
