import typing as ty
from functools import singledispatchmethod

import openai

from src.app.actor import Actor, ActorRef, System
from src.app.gpt.user import (
    ChatMessage,
    ChatMessageSent,
    ChatSession,
    CompletionModels,
    CreateSession,
    CreateUser,
    SendChatMessage,
    SessionCreated,
    User,
    UserCreated,
)
from src.app.journal import Journal
from src.app.utils.fmtutils import fprint
from src.domain.config import Settings
from src.domain.model import Command, Event, Message
from src.infra.mq import MailBox


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


class OpenAIClient:  # TODO: this might be an (Actor):
    def __init__(self, api_key: str):
        self.__api_key = api_key
        self.client = openai.ChatCompletion
        self.messages = list()

    def send(
        self,
        message: ChatMessage,
        model: CompletionModels,
        stream: bool = True,
        **kwargs: CompletionOptions,
    ):
        self.messages.append(message.asdict())
        resp = self.client.create(
            api_key=self.__api_key,
            messages=self.messages,
            model=model,
            stream=stream,
            **kwargs,
        )
        return resp

    @classmethod
    def from_config(cls, config: Settings):
        return cls(api_key=config.OPENAI_API_KEY)


class SystemStarted(Event):
    settings: Settings


class GPTSystem(System):
    childs: dict[ActorRef, "Actor"]

    def __init__(self, mailbox: MailBox, settings: Settings):
        super().__init__(mailbox=mailbox)
        self.settings=settings

    @System.handle.register
    async def _(self, command: CreateUser):
        self.create_child(command)

    def create_child(self, command: CreateUser) -> "UserActor":
        event = UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity.entity_id] = user_actor
        self.collect(event)
        return user_actor

    def create_journal(self):
        journal = Journal.build(db_url=self.settings.db.ASYNC_DB_URL)
        self.childs["journal"] = journal

    @property
    def journal(self) -> Journal:
        return self.system.childs["journal"] # type: ignore

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SystemStarted):
        return cls(mailbox=MailBox.build(), settings=event.settings)

    @classmethod
    def setup(cls, settings: Settings):
        event = SystemStarted(entity_id="system", settings=settings)
        system: GPTSystem = cls.apply(event)
        system.create_journal()
        system.collect(event)
        return system


class UserActor(Actor):
    entity: User
    childs: dict[ActorRef, "SessionActor"]

    def __init__(self, user: User):
        super().__init__(mailbox=MailBox.build())
        self.entity = user

    def create_child(self, command: CreateSession) -> "SessionActor":
        event = SessionCreated(user_id=command.user_id, session_id=command.entity_id)
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity.entity_id] = session_actor
        self.collect(event)
        return session_actor

    @singledispatchmethod
    async def handle(self, command: Command):
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @handle.register
    async def _(self, command: CreateSession):
        self.create_child(command)

    @apply.register
    @classmethod
    def _(cls, event: UserCreated):
        return cls(user=User.apply(event))


class SessionActor(Actor):
    entity: ChatSession

    def __init__(self, chat_session: ChatSession):  # , model_client: OpenAIClient):
        super().__init__(mailbox=MailBox.build())
        self.entity = chat_session
        self.model_client: OpenAIClient = OpenAIClient.from_config(
            Settings.from_file("settings.toml")
        )

    def send(self, message: ChatMessage, model: CompletionModels, stream=True):
        chunks = self.model_client.send(message=message, model=model, stream=stream)

        for resp in chunks:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                yield content

    def display_message(self, answer: ty.Generator) -> str:
        str_container = ""
        for chunk in answer:
            if chunk is None:
                fprint("\n")
            else:
                fprint(chunk)
                str_container += chunk
        return str_container

    @singledispatchmethod
    async def handle(self, message: Message):
        raise NotImplementedError

    @handle.register
    async def _(self, command: SendChatMessage):
        chunks = self.send(message=command.chat_message, model=command.model)
        event = ChatMessageSent(
            entity_id=self.entity.user_id,
            session_id=self.entity.entity_id,
            chat_message=command.chat_message,
        )
        self.collect(event)
        self.display_message(chunks)

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SessionCreated):
        return cls(chat_session=ChatSession.apply(event))
