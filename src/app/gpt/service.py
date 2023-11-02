import asyncio
import typing as ty
from functools import singledispatchmethod

import openai

from src.app.actor import Actor, ActorRef, EventLog, System
from src.app.gpt import model
from src.app.journal import EventStore, Journal
from src.app.utils.fmtutils import fprint
from src.domain.config import Settings
from src.domain.model import Command, Event, Message
from src.infra.mq import MailBox


def display_message(answer: ty.Generator[str, None, None]) -> str:
    str_container = ""
    for chunk in answer:
        if chunk is None:
            fprint("\n")
        else:
            fprint(chunk)
            str_container += chunk
    return str_container


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
    # https://medium.com/@colemanhindes/unofficial-gpt-3-developer-faq-fcb770710f42
    # How many concurrent requests can I make to the API?:

    # Only 2 concurrent requests can be made per API key at a time.
    def __init__(self, api_key: str):
        self.__api_key = api_key
        self.client = openai.ChatCompletion
        self.messages = list()

    def send(
        self,
        message: model.ChatMessage,
        model: model.CompletionModels,
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


class SystemCreated(Event):
    ...


class SystemStarted(Event):
    settings: Settings


class SystemStoped(Event):
    ...


class GPTSystem(System):
    childs: dict[ActorRef, "Actor"]

    def __init__(self, mailbox: MailBox, settings: Settings):
        super().__init__(mailbox=mailbox)
        self.settings = settings

    async def create_child(self, command: model.CreateUser) -> "UserActor":
        event = model.UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity.entity_id] = user_actor
        await self.publish(event)
        return user_actor

    def create_journal(self, eventstore: EventStore, mailbox: MailBox):
        "journal is part of the application layer, so it should be created here by gptsystem"
        journal = Journal(eventstore, mailbox)
        self.childs["journal"] = journal

    @classmethod
    async def create(cls, settings: Settings, eventstore: EventStore | None = None):
        if eventstore is None:
            eventstore = EventStore.build(db_url=settings.db.ASYNC_DB_URL)

        event = SystemStarted(entity_id="system", settings=settings)
        system: GPTSystem = cls.apply(event)
        system.create_eventlog()
        system.create_journal(
            eventstore=eventstore,
            mailbox=MailBox.build(),
        )
        # await system.publish(event)
        return system

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SystemStarted):
        return cls(mailbox=MailBox.build(), settings=event.settings)

    @singledispatchmethod
    async def handle(self, command: Command):
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage):
        user = self.get_actor(command.user_id)
        if not user:
            create_user = model.CreateUser(user_id=command.user_id)
            user = await self.create_child(create_user)

        session = user.get_actor(command.entity_id)
        if not session:
            create_session = model.CreateSession(
                user_id=command.user_id, session_id=command.entity_id
            )
            session = await user.create_child(create_session)

        await session.handle(command)

    @handle.register
    async def _(self, command: model.CreateUser):
        await self.create_child(command)

    async def stop(self):
        ...
        # await self.publish(SystemStoped(entity_id="system"))


class UserActor(Actor):
    entity: model.User
    childs: dict[ActorRef, "SessionActor"]

    def __init__(self, user: model.User):
        super().__init__(mailbox=MailBox.build())
        self.entity = user

    async def create_child(self, command: model.CreateSession) -> "SessionActor":
        event = model.SessionCreated(
            user_id=command.user_id, session_id=command.entity_id
        )
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity_id] = session_actor
        await self.publish(event)
        return session_actor

    @singledispatchmethod
    async def handle(self, command: Command):
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.CreateSession):
        session_actor = await self.create_child(command)
        self.entity.add_session(session=session_actor.entity)

    @apply.register
    @classmethod
    def _(cls, event: model.UserCreated):
        return cls(user=model.User.apply(event))


class SessionActor(Actor):
    entity: model.ChatSession

    def __init__(self, chat_session: model.ChatSession):
        super().__init__(mailbox=MailBox.build())
        self.entity = chat_session
        self.model_client: OpenAIClient = OpenAIClient.from_config(
            Settings.from_file("settings.toml")
        )

    def send(
        self, message: model.ChatMessage, model: model.CompletionModels, stream=True
    ) -> ty.Generator[str, None, None]:
        chunks = self.model_client.send(message=message, model=model, stream=stream)

        for resp in chunks:
            for choice in resp.choices:  # type: ignore
                content = choice.get("delta", {}).get("content")
                yield content

    @singledispatchmethod
    async def handle(self, message: Message):
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage):
        chunks = self.send(message=command.chat_message, model=command.model)
        event = model.ChatMessageSent(
            session_id=self.entity_id,
            chat_message=command.chat_message,
        )
        self.entity.apply(event)
        await self.publish(event)

        answer = display_message(chunks)
        model.ChatResponseReceived(
            session_id=self.entity_id,
            chat_message=model.ChatMessage(role="assistant", content=answer),
        )

        await self.publish(event)

    @singledispatchmethod
    def apply(self, event: Event):
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: model.SessionCreated):
        return cls(chat_session=model.ChatSession.apply(event))
