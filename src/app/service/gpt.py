import typing as ty
from enum import Enum
from pathlib import Path

import openai
from pydantic import BaseModel

from src.domain.model.name_tools import str_to_snake


def enum_generator(
    **kwargs: dict[str, ty.Iterable[str]]
) -> ty.Generator[Enum, None, None]:
    """
    Example:
    -----
    >>> enum_gen = enum_generator(Color=["red", "green", "blue"])
    Color = next(enum_gen)
    assert issubclass(Color, Enum)
    assert isinstance(Color.red, Color)
    assert Color.red.value == "red"
    """
    for name, values in kwargs.items():
        yield Enum(name, {str_to_snake(v): v for v in values})


class ModelEndpoint(BaseModel):
    endpoint: Path
    models: tuple[str, ...]


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


class CompletionEndPoint(ModelEndpoint):
    endpoint: Path = Path("/v1/chat/completion")
    model: CompletionModels


class CompletionOptions(ty.TypedDict, total=False):
    model: str
    message: list
    functions: list
    function_call: str
    temperature: float
    top_p: float
    n: int
    stream: bool
    stop: str | list | None
    max_tokens: int
    presence_penalty: float
    frequency_penalty: float
    logit_bias: dict
    user: str


from src.app.actor import Actor, ActorRef
from src.domain.config import Settings
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
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox, QueueBroker

"""
                SystemActor
                /
            ChatBotActor
            /
        UserActor
        /
    SessionActor
"""


class ChatMessage(ValueObject):
    role: ty.Literal["system", "user", "assistant", "functio"]
    content: str


class CreateSession(Command):
    owner_id: str
    session_id: str


class SessionCreated(Event):
    user_id: str
    entity_id: str = Field(alias="session_id")


class ChatSession(Entity):
    session_id: str = Field(alias="entity_id", default_factory=uuid_factory)
    user_id: str
    messages: list[ChatMessage] = Field(default_factory=list)

    def handle(self, command: Command):
        if command is SendChatMessage:
            ...

    @Entity.apply.register
    @classmethod
    def _(cls, event: SessionCreated):
        return cls(entity_id=event.entity_id, user_id=event.user_id)


class CreateUser(Command):
    entity_id: str = Field(alias="user_id")


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")


class SendChatMessage(Command):
    user_message: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True

    @computed_field
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(role="user", content=self.user_message)


class ChatMessageSent(Event):
    session_id: str


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


class OpenAIClient:
    def __init__(self, api_key: str):
        self.__api_key = api_key
        self.client = openai.ChatCompletion
        self.messages = list()

    def send(self, message: ChatMessage, model: CompletionModels, stream: bool = True):
        self.messages.append(message.asdict())
        resp = self.client.create(
            api_key=self.__api_key, messages=self.messages, model=model, stream=stream
        )
        return resp

    @classmethod
    def from_config(cls, config: Settings):
        return cls(api_key=config.OPENAI_API_KEY)


class SessionActor(Actor):
    def __init__(self, chat_session: ChatSession):
        self.chat_session = chat_session
        self.model_client: OpenAIClient = ...

    def handle(self, message: Message):
        if type(message) is SendChatMessage:
            chunks = self.send(message=message.chat_message, model=message.model)
            for chunk in chunks:
                print(chunk, end="")

    def send(self, message: ChatMessage, model: CompletionModels, stream=True):
        chunks = self.model_client.send(message=message, model=model, stream=stream)

        for resp in chunks:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                yield content

    @classmethod
    def from_event(cls, event: SessionCreated):
        return cls(chat_session=ChatSession.apply(event))


class UserActor(Actor):
    def __init__(self, user: User):
        self.user = user
        self.childs: dict[ActorRef, SessionActor] = dict()

    def handle(self, message: Message):
        if isinstance(message, Command):
            self.user.handle(message)
        elif isinstance(message, Event):
            self.user.apply(message)

    @classmethod
    def from_event(cls, event: UserCreated):
        return cls(user=User.apply(event))

    def create_session(self, session_id: str, user_id: str):
        event = SessionCreated(session_id=session_id, user_id=user_id)
        session_actor = SessionActor.from_event(event)
        self.childs[session_actor.chat_session.entity_id] = session_actor

    def get_session(self, session_id: str, user_id):
        if (session_actor := self.childs.get(session_id, None)) is None:
            session_actor = self.create_session(session_id, user_id)
        return session_actor


class System(Actor):
    def __init__(self, model_client: OpenAIClient):
        self.model_client = model_client
        self.childs: dict[ActorRef, UserActor] = dict()

    def handle(self, command: Command):
        ...

    def create_user(self, user_id: str) -> UserActor:
        event = UserCreated(user_id=user_id)
        user_actor = UserActor.from_event(event)
        self.childs[user_actor.user.entity_id] = user_actor
        return user_actor

    def get_user(self, user_id: ActorRef):
        if (user_actor := self.childs.get(user_id, None)) is None:
            user_actor = self.create_user(user_id)
        return user_actor


def setup_system():
    settings = Settings.from_file("settings.toml")
    system = System(model_client=OpenAIClient.from_config(settings))
    return system
