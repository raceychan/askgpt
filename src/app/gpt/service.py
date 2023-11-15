import typing as ty
from contextlib import asynccontextmanager
from functools import singledispatchmethod

from src.app.actor import EntityActor, EventLog, System
from src.app.gpt import model
from src.app.gpt.client import OpenAIClient
from src.app.journal import Journal
from src.app.utils.fmtutils import fprint
from src.domain._log import logger
from src.domain.config import Settings
from src.domain.interface import ICommand, ISettings
from src.domain.model import Command, Event, Message
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox
from src.infra.sa_utils import async_engine_factory
from src.infra.schema import EventSchema


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


class GPTSystem(System["UserActor"]):
    def __init__(self, mailbox: MailBox, settings: ISettings):
        super().__init__(mailbox=mailbox, settings=settings)

    async def create_user(self, command: model.CreateUser) -> "UserActor":
        event = model.UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity_id] = user_actor
        await self.publish(event)
        return user_actor

    def setup_journal(self, eventstore: EventStore, mailbox: MailBox) -> None:
        """
        journal is part of the application layer, it should be created here by gptsystem
        """
        journal_ref = self.settings.actor_refs.JOURNAL
        journal = Journal(eventstore, mailbox, ref=journal_ref)
        self._journal = journal

    async def rebuild_user(self, user_id: str):
        events = await self.journal.list_events(user_id)
        created = model.UserCreated(user_id=user_id)
        user_actor = UserActor.apply(created)
        user_actor.rebuild(events)
        self.childs[user_actor.entity_id] = user_actor
        return user_actor

    @classmethod
    async def create(cls, settings: Settings, eventstore: EventStore) -> "GPTSystem":
        event = SystemStarted(entity_id=settings.actor_refs.SYSTEM, settings=settings)
        system: GPTSystem = cls.apply(event)
        system.setup_journal(eventstore=eventstore, mailbox=MailBox.build())

        # await system.publish(event)
        return system

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @apply.register
    @classmethod
    def _(cls, event: SystemStarted) -> ty.Self:
        return cls(mailbox=MailBox.build(), settings=event.settings)  # type: ignore # pydantic forces concrete settings

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage) -> None:
        # TODO: rebuild user before creating them

        user: "UserActor" | None = self.get_child(command.user_id)
        if not user:
            user = await self.rebuild_user(command.user_id)
            # user = self.select_child(command.user_id)

        breakpoint()
        # session = user.get_child(command.entity_id)
        # if not session:
        #     create_session = model.CreateSession(
        #         user_id=command.user_id, session_id=command.entity_id
        #     )
        #     await user.handle(create_session)
        #     session = user.select_child(command.entity_id)

        # await session.handle(command)

    @handle.register
    async def _(self, command: model.CreateUser) -> None:
        await self.create_user(command)

    async def stop(self) -> None:
        # await self.publish(SystemStoped(entity_id="system"))
        logger.info("system stopped")
        # raise NotImplementedError


class UserActor(EntityActor["SessionActor", model.User]):
    def __init__(self, user: model.User):
        super().__init__(mailbox=MailBox.build(), entity=user)

    def create_session(self, event: model.SessionCreated) -> "SessionActor":
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity_id] = session_actor
        self.entity.apply(event)
        return session_actor

    async def rebuild_sessions(self):
        for session_id in self.entity.session_ids:
            await self.rebuild_session(session_id)

    async def rebuild_session(self, session_id: str) -> "SessionActor":
        events = await self.system.journal.list_events(session_id)
        created = self.entity.predict_command(
            model.CreateSession(session_id=session_id, user_id=self.entity_id)
        )[0]
        session_actor = SessionActor.apply(created)
        session_actor.rebuild(events)
        self.childs[session_actor.entity_id] = session_actor
        return session_actor

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.CreateSession) -> None:
        events = self.entity.predict_command(command)
        self.create_session(events[0])
        for e in events:
            await self.publish(e)

    @apply.register
    @classmethod
    def _(cls, event: model.UserCreated) -> ty.Self:
        return cls(user=model.User.apply(event))

    @apply.register
    def _(self, event: model.SessionCreated) -> ty.Self:
        self.entity.apply(event)
        return self

    @property
    def session_count(self):
        return len(self.entity.session_ids)


class SessionActor(EntityActor[OpenAIClient, model.ChatSession]):
    # TODO: openai should be childs of system, not session
    def __init__(self, chat_session: model.ChatSession):
        super().__init__(mailbox=MailBox.build(), entity=chat_session)

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

    async def _send_chat(
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

    @property
    def message_count(self) -> int:
        return len(self.entity.messages)

    @singledispatchmethod
    async def handle(self, message: Message) -> None:
        raise NotImplementedError

    def predict_command(self, command: ICommand) -> model.ChatMessageSent:
        if isinstance(command, model.SendChatMessage):
            return model.ChatMessageSent(
                session_id=self.entity_id, chat_message=command.chat_message
            )
        else:
            raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage) -> None:
        chunks = self._send_chat(message=command.chat_message, model=command.model)
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

        self.entity.apply(response_received)
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


@asynccontextmanager
async def setup_system(settings: Settings):
    engine = async_engine_factory(
        settings.db.ASYNC_DB_URL,
        echo=True,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )
    await EventSchema.create_table_async(engine)
    await EventSchema.assure_table_exist(engine)

    eventstore = EventStore(engine=engine)
    system = await GPTSystem.create(settings=settings, eventstore=eventstore)

    try:
        yield system
    except KeyboardInterrupt:
        logger.info("Quit by user")
    finally:
        await system.stop()


class GPTService:
    ...
