import enum
import typing as ty
from contextlib import asynccontextmanager
from functools import singledispatchmethod

from src.app.actor import EntityActor, System
from src.app.bootstrap import bootstrap
from src.app.gpt import model, repository
from src.app.gpt.client import OpenAIClient
from src.app.journal import Journal
from src.app.utils.fmtutils import async_receiver
from src.domain import encrypt
from src.domain._log import logger
from src.domain.config import Settings
from src.domain.interface import ICommand, ISettings
from src.domain.model import Command, Event, Message
from src.infra.eventstore import EventStore
from src.infra.mq import MailBox
from src.infra.sa_utils import async_engine_factory


class SystemStarted(Event):
    settings: Settings


class SystemStoped(Event):
    ...


class UserNotRegisteredError(Exception):
    ...


class OrphanSessionError(Exception):
    def __init__(self, session_id: str, user_id: str):
        msg = f"Session {session_id} does not belong to user {user_id}"
        super().__init__(msg)


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
        if session_id not in self.entity.session_ids:
            raise OrphanSessionError(session_id, self.entity_id)

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
        raise NotImplementedError(f"apply for {event} is not implemented")

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

        answer = await async_receiver(chunks)
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


class Authenticator:
    def __init__(self, user_id: str, session_id: str = ""):
        self.user_id = user_id
        self.session_id = session_id
        self._is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    def authenticate(self):
        self._is_authenticated = True


class GPTSystem(System[UserActor]):
    def __init__(self, mailbox: MailBox, settings: ISettings):
        super().__init__(mailbox=mailbox, settings=settings)

    async def create_user(self, command: model.CreateUser) -> "UserActor":
        event = model.UserCreated(
            user_id=command.entity_id, user_info=command.user_info
        )
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

    async def rebuild_user(self, user_id: str) -> "UserActor":
        events = await self.journal.list_events(user_id)
        if not events:
            raise UserNotRegisteredError(f"No events for user: {user_id}")
        created = events.pop(0)
        user_actor = UserActor.apply(created)
        user_actor.rebuild(events)
        self.childs[user_actor.entity_id] = user_actor
        return user_actor

    # @classmethod
    async def start(self, eventstore: EventStore) -> "GPTSystem":
        event = SystemStarted(
            entity_id=self.settings.actor_refs.SYSTEM, settings=self.settings  # type: ignore
        )
        self.apply(event)
        self.setup_journal(eventstore=eventstore, mailbox=MailBox.build())
        return self

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

        session = user.get_child(command.entity_id)
        if not session:
            session = await user.rebuild_session(command.entity_id)

        await session.handle(command)

    @handle.register
    async def _(self, command: model.CreateUser) -> None:
        await self.create_user(command)

    async def stop(self) -> None:
        # await self.publish(SystemStoped(entity_id="system"))
        ...

        logger.info("system stopped")


class ServiceState(enum.Enum):
    class InvalidStateError(Exception):
        ...

    created = enum.auto()
    running = enum.auto()
    stopped = enum.auto()

    @property
    def is_running(self) -> bool:
        return self == ServiceState.running

    @property
    def is_created(self) -> bool:
        return self == ServiceState.created

    @property
    def is_stopped(self) -> bool:
        return self == ServiceState.stopped

    def start(self) -> ty.Self:
        if not self.is_created:
            raise self.InvalidStateError("system already started")
        return ServiceState.running

    def stop(self) -> ty.Self:
        if not self.is_running:
            raise self.InvalidStateError("system already stopped")
        return ServiceState.stopped


class GPTService:
    auth: Authenticator

    def __init__(
        self,
        system: GPTSystem,
        user_repo: repository.UserRepository,
    ):
        self._state = ServiceState.created
        self._system: GPTSystem = system
        self._user_repo = user_repo

    async def send_question(self, question: str) -> None:
        command = model.SendChatMessage(
            user_id=self.auth.user_id,
            session_id=self.auth.session_id,
            message_body=question,
            role="user",
        )

        await self.system.receive(command)

    async def interactive(self) -> None:
        while True:
            question = input("\nwhat woud you like to ask?\n\n")
            await self.send_question(question)

    async def login(self, email: str, password: str):
        if not email:
            raise Exception("email is required")

        user = await self._user_repo.search_user_by_email(email)
        if not user:
            raise Exception("user not found")

        self.auth = Authenticator(user_id=user.entity_id)

    async def create_user(self, username: str, useremail: str, password: str) -> None:
        """
        TODO: create the user in user_schema
        """
        user_info: model.UserInfo = model.UserInfo(
            user_name=username,
            user_email=useremail,
            hash_password=encrypt.hash_password(password.encode()),
        )
        user_id, session_id = model.uuid_factory(), model.uuid_factory()
        create_user = model.CreateUser(user_id=user_id, user_info=user_info)
        await self.system.receive(create_user)

        await self.user_create_session(user_id=user_id, session_id=session_id)
        # self.auth = Authenticator(user_id=user_id, session_id=session_id)

    async def user_create_session(self, user_id: str, session_id: str):
        user_actor = self.system.select_child(user_id)
        await user_actor.handle(
            model.CreateSession(user_id=user_id, session_id=session_id)
        )

    async def find_user(self, username: str, useremail: str) -> model.User | None:
        """
        make sure user does not exist
        """
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    @property
    def system(self) -> GPTSystem:
        return self._system  # type: ignore

    @property
    def state(self) -> ServiceState:
        return self._state

    @state.setter
    def state(self, state: ServiceState) -> None:
        if self._state is ServiceState.stopped:
            raise Exception("system already stopped")
        self._state = state

    async def start(self) -> None:
        if self.state is ServiceState.running:
            return

        await bootstrap(self._user_repo.aioengine)
        await self.system.start(
            eventstore=EventStore(aioengine=self._user_repo.aioengine),
        )
        logger.info("System started")
        self.state = self.state.start()

    async def stop(self):
        await self.system.stop()
        self.state.stop()

    @asynccontextmanager
    async def setup_system(self):
        try:
            await self.start()
            yield self
        except KeyboardInterrupt:
            logger.info("Quit by user")
        finally:
            await self.stop()

    @classmethod
    def build(cls, settings: Settings) -> ty.Self:
        engine = async_engine_factory(
            settings.db.ASYNC_DB_URL,
            echo=settings.db.ENGINE_ECHO,
            isolation_level=settings.db.ISOLATION_LEVEL,
            pool_pre_ping=True,
        )
        system = GPTSystem(settings=settings, mailbox=MailBox.build())
        user_repo = repository.UserRepository(aioengine=engine)
        service = cls(system=system, user_repo=user_repo)
        return service
