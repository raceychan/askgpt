import typing as ty
from enum import Enum
from pathlib import Path

import openai
from pydantic import BaseModel

from src.domain.config import settings
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


"""
                SystemActor
                /
            ChatBotActor
            /
        UserActor
        /
    SessionActor
"""


from src.app.actor import Actor
from src.domain.config import Settings
from src.domain.model import (
    Command,
    Entity,
    Event,
    Field,
    Message,
    computed_field,
    uuid_factory,
)
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox, QueueBroker


# @frozenclass
class ChatMessage(Message):
    role: ty.Literal["system", "user", "assistant", "functio"]
    content: str


class ChatSession(Entity):
    session_id: str = Field(alias="entity_id", default_factory=uuid_factory)
    user_id: str
    messages: list[ChatMessage] = Field(default_factory=list)


# class UserEvent(Event):
#     event_registry: ty.ClassVar[dict] = dict()


class UserCreated(Event):
    entity_id: str = Field(alias="user_id")


# aggregate_root
class User(Entity):
    entity_id: str = Field(alias="user_id")
    chat_sessions: dict[str, ChatSession] = Field(default_factory=dict)

    def add_new_session(self):
        new_session = ChatSession(user_id=self.user_id)  # type: ignore
        self.chat_sessions[new_session.session_id] = new_session

    def handle(self, command):
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


class AbstractRef:
    ...


ActorRef = ty.Annotated[str, AbstractRef, "ActorRef"]


class SessionActor(Actor):
    def __init__(self, session: ChatSession):
        self.session = session

    def handle(self, message: Message):
        ...


class UserActor(Actor):
    def __init__(self, user: User):
        self.user = user
        self.childs: dict[ActorRef, SessionActor] = dict()

    def handle(self, message: Message):
        ...


class SendChatMessage(Command):
    user_message: str
    model: CompletionModels = "gpt-3.5-turbo"
    stream: bool = True

    @computed_field
    @property
    def chat_message(self) -> ChatMessage:
        return ChatMessage(role="user", content=self.user_message)


class System(Actor):
    def __init__(self, model_client: OpenAIClient):
        self.model_client = model_client
        self.childs: dict[ActorRef, UserActor] = dict()

    def handle(self, command: Command):
        if type(command) is SendChatMessage:
            for msg in self.send(message=command.chat_message, model=command.model):
                print(msg, end="")

    def send(self, message: ChatMessage, model: CompletionModels, stream=True):
        chunks = self.model_client.send(message=message, model=model, stream=stream)

        for resp in chunks:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                yield content

    def add_user(self, user: User):
        self.childs[user.entity_id] = UserActor(user=user)
