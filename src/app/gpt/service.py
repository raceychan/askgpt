import asyncio
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
from src.app.journal import EventStore, Journal
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
        self.settings = settings

    @System.handle.register
    async def _(self, command: CreateUser):
        await self.create_child(command)

    async def create_child(self, command: CreateUser) -> "UserActor":
        event = UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity.entity_id] = user_actor
        await self.publish(event)
        return user_actor

    def create_journal(self, eventstore: EventStore, mailbox: MailBox):
        journal = Journal(eventstore, mailbox)
        self.childs["journal"] = journal
    
    def set_journal(self, journal: Journal):
        self.system.childs["journal"] = journal

    @property
    def journal(self):
        try:
            journal_ = self.system.childs["journal"]
        except KeyError as ke:
            raise Exception("Journal not created") from ke
        return journal_

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SystemStarted):
        return cls(mailbox=MailBox.build(), settings=event.settings)

    @classmethod
    async def create(cls, settings: Settings):
        event = SystemStarted(entity_id="system", settings=settings)
        system: GPTSystem = cls.apply(event)
        asyncio.create_task(system.publish_started_event(event))
        return system

    async def publish_started_event(self, event: SystemStarted):
        await self._journal_started_event.wait()
        await self.publish(event)



class UserActor(Actor):
    entity: User
    childs: dict[ActorRef, "SessionActor"]

    def __init__(self, user: User):
        super().__init__(mailbox=MailBox.build())
        self.entity = user

    async def create_child(self, command: CreateSession) -> "SessionActor":
        event = SessionCreated(user_id=command.user_id, session_id=command.entity_id)
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity.entity_id] = session_actor
        await self.publish(event)
        return session_actor

    @singledispatchmethod
    async def handle(self, command: Command):
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @handle.register
    async def _(self, command: CreateSession):
        await self.create_child(command)

    @apply.register
    @classmethod
    def _(cls, event: UserCreated):
        return cls(user=User.apply(event))


class SessionActor(Actor):
    entity: ChatSession

    def __init__(self, chat_session: ChatSession):
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
        await self.publish(event)
        self.display_message(chunks)

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SessionCreated):
        return cls(chat_session=ChatSession.apply(event))
