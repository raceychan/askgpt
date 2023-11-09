import typing as ty
from functools import singledispatchmethod

from src.domain import Command, Event, Message, Settings
from src.domain.interface import ISettings
from src.infra import MailBox

from ..actor import EntityActor, System
from ..gpt import model

# from ..interface import ActorRef, ActorRegistry
from ..journal import EventStore, Journal
from ..utils import fprint
from .client import OpenAIClient


def display_message(answer: ty.Generator[str | None, None, None]) -> str:
    str_container = ""
    for chunk in answer:
        if chunk is None:
            fprint("\n")
        else:
            fprint(chunk)
            str_container += chunk
    return str_container


async def async_display_message(answer: ty.AsyncGenerator[str | None, None]) -> str:
    str_container = ""
    async for chunk in answer:
        if chunk is None:
            fprint("\n")
        else:
            fprint(chunk)
            str_container += chunk
    return str_container


# class AIClient(ty.Protocol):
#     async def send_chat(self, message: model.ChatMessage, **kwargs: CompletionOptions)->ty.:
#         ...


class SystemCreated(Event):
    ...


class SystemStarted(Event):
    settings: Settings


class SystemStoped(Event):
    ...


class GPTSystem(System):
    def __init__(self, mailbox: MailBox, settings: ISettings):
        super().__init__(mailbox=mailbox, settings=settings)
        self.__journal_ref = settings.actor_refs.JOURNAL

    async def create_user(self, command: model.CreateUser) -> "UserActor":
        event = model.UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity_id] = user_actor
        await self.publish(event)
        return user_actor

    def create_journal(self, eventstore: EventStore, mailbox: MailBox) -> None:
        """journal is part of the application layer,
        so it should be created here by gptsystem"""
        journal = Journal(eventstore, mailbox)
        self.childs[self.__journal_ref] = journal

    @property
    def journal(self) -> Journal:
        return self.childs[self.__journal_ref]  # type: ignore

    @classmethod
    async def create(
        cls, settings: Settings, eventstore: EventStore | None = None
    ) -> "GPTSystem":
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
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SystemStarted) -> ty.Self:
        return cls(mailbox=MailBox.build(), settings=event.settings)  # type: ignore # pydantic can't handle protocol, event has to have a concrete settings

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage) -> None:
        user: "UserActor" | None = self.get_child(command.user_id)
        # TODO: rebuild user before creating them
        if not user:
            create_user = model.CreateUser(user_id=command.user_id)
            user = await self.create_user(create_user)

        session = user.get_child(command.entity_id)
        if not session:
            create_session = model.CreateSession(
                user_id=command.user_id, session_id=command.entity_id
            )
            session = await user.create_session(create_session)

        await session.handle(command)

    @handle.register
    async def _(self, command: model.CreateUser) -> None:
        await self.create_user(command)

    async def stop(self) -> None:
        ...
        # await self.publish(SystemStoped(entity_id="system"))


class UserActor(EntityActor[model.User]):
    def __init__(self, user: model.User):
        super().__init__(mailbox=MailBox.build(), entity=user)

    async def create_session(self, command: model.CreateSession) -> "SessionActor":
        event = model.SessionCreated(
            user_id=command.user_id, session_id=command.entity_id
        )
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity_id] = session_actor
        await self.publish(event)
        return session_actor

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.CreateSession) -> None:
        session_actor = await self.create_session(command)
        self.entity.add_session(session=session_actor.entity)

    @apply.register
    @classmethod
    def _(cls, event: model.UserCreated) -> ty.Self:
        return cls(user=model.User.apply(event))


class SessionActor(EntityActor[model.ChatSession]):
    def __init__(self, chat_session: model.ChatSession):
        super().__init__(mailbox=MailBox.build(), entity=chat_session)
        # self.childs = ActorRegistry[ActorRef, OpenAIClient]()

    @property
    def chat_context(self) -> list[model.ChatMessage]:
        return self.entity.messages

    def get_model_client(self) -> OpenAIClient:
        model_client = self.get_child("model_client")
        if model_client is None:
            model_client = OpenAIClient.from_apikey(self.system.settings.OPENAI_API_KEY)
            self.set_model_client(model_client)
        return model_client

    def set_model_client(self, client: OpenAIClient) -> None:
        if self.get_child("model_client"):
            raise Exception("model_client already set")
        self.childs["model_client"] = client

    async def send_chat(
        self,
        message: model.ChatMessage,
        model: model.CompletionModels,
        stream: bool = True,
    ) -> ty.AsyncGenerator[str | None, None]:
        client = self.get_model_client()
        chunks = await client.send_chat(
            messages=self.chat_context + [message], model=model, stream=stream
        )

        async for resp in chunks:
            for choice in resp.choices:
                content = choice.delta.content
                yield content

    @singledispatchmethod
    async def handle(self, message: Message) -> None:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage) -> None:
        chunks = self.send_chat(message=command.chat_message, model=command.model)
        event = model.ChatMessageSent(
            session_id=self.entity_id,
            chat_message=command.chat_message,
        )
        self.entity.apply(event)
        await self.publish(event)

        answer = await async_display_message(chunks)
        response_received = model.ChatResponseReceived(
            session_id=self.entity_id,
            chat_message=model.ChatMessage(role="assistant", content=answer),
        )

        await self.publish(response_received)

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    def _(self, event: model.ChatMessageSent) -> ty.Self:
        self.entity.apply(event)
        return self

    @apply.register
    @classmethod
    def _(cls, event: model.SessionCreated) -> ty.Self:
        return cls(chat_session=model.ChatSession.apply(event))


async def setup_system(settings: Settings) -> GPTSystem:
    eventstore = EventStore.build(db_url=settings.db.ASYNC_DB_URL)
    system_started = SystemStarted(entity_id="system", settings=settings)
    system = GPTSystem.apply(system_started)
    system.create_eventlog()
    system.create_journal(eventstore=eventstore, mailbox=MailBox.build())
    return system
