import enum
import typing as ty
from contextlib import asynccontextmanager
from functools import cached_property, singledispatchmethod

from src.app.actor import (
    BoxFactory,
    EntityActor,
    Journal,
    QueueBox,
    StatefulActor,
    System,
)
from src.app.auth.model import UserSignedUp
from src.app.gpt import errors, gptclient, model
from src.domain._log import logger
from src.domain.config import Settings
from src.domain.fmtutils import async_receiver
from src.domain.interface import ActorRef, ICommand
from src.domain.model.base import Command, Event, Message
from src.infra import cache, eventstore, factory


class SystemStarted(Event):
    settings: Settings


class SystemStoped(Event):
    ...


class SystemState(enum.Enum):
    created = enum.auto()
    running = enum.auto()
    stopped = enum.auto()

    @property
    def is_running(self) -> bool:
        return self == type(self).running

    @property
    def is_created(self) -> bool:
        return self == type(self).created

    @property
    def is_stopped(self) -> bool:
        return self == type(self).stopped

    def start(self) -> "SystemState":
        if not self.is_created:
            raise errors.InvalidStateError("system already started")
        return type(self).running

    def stop(self) -> "SystemState":
        if self.is_created:
            raise errors.InvalidStateError("system not started yet")
        if not self.is_running:
            raise errors.InvalidStateError("system already stopped")
        return type(self).stopped


class GPTBaseActor[TChild: ty.Any, TEntity: ty.Any](
    EntityActor[TChild, TEntity], StatefulActor[TChild, TEntity]
):
    system: "GPTSystem"


class UserActor(GPTBaseActor["SessionActor", model.User]):
    def __init__(self, user: model.User):
        super().__init__(boxfactory=QueueBox, entity=user)
        self.user_api_pool = None
        self._keyspace = self.system.settings.redis.KEY_SPACE("apikeypool")

    def get_user_api_pool(self):
        if self.user_api_pool is not None:
            return self.user_api_pool

        user_api_pool = gptclient.APIPool(
            pool_key=self.apipool_key,
            api_keys=self.decrypt_openai_keys(),
            redis=self.system.cache,  # type: ignore
        )
        self.user_api_pool = user_api_pool
        return self.user_api_pool

    @cached_property
    def apipool_key(self) -> str:
        return self._keyspace(self.entity_id).key

    def create_session(self, event: model.SessionCreated) -> "SessionActor":
        session_actor = SessionActor.apply(event)
        self.childs[session_actor.entity_id] = session_actor
        self.entity.apply(event)
        return session_actor

    async def rebuild_sessions(self):
        for session_id in self.entity.session_ids:
            yield await self.rebuild_session(session_id)

    async def rebuild_session(self, session_id: str) -> "SessionActor":
        if session_id not in self.entity.session_ids:
            raise errors.OrphanSessionError(session_id, self.entity_id)

        events = await self.system.journal.list_events(session_id)
        created = self.entity.predict_command(
            model.CreateSession(session_id=session_id, user_id=self.entity_id)
        )[0]
        session_actor = SessionActor.apply(created)
        if events:
            session_actor.rebuild(events)
            self.childs[session_actor.entity_id] = session_actor
        return session_actor

    def decrypt_openai_keys(self):
        if not self.entity.api_keys:
            raise errors.APIKeyNotProvidedError(self.entity_id)
        openai_keys = self.entity.api_keys["openai"]
        encryptor = factory.get_encrypt(self.system.settings)
        keys = tuple(encryptor.decrypt_string(key.encode()) for key in openai_keys)
        return keys

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def apply(self, unknown: object) -> ty.Self:
        raise NotImplementedError(f"apply for {unknown} is not implemented")

    @apply.register
    @classmethod
    def _(cls, unknown: object) -> ty.Self:
        raise NotImplementedError(f"apply for {unknown} is not implemented")

    @handle.register
    async def _(self, command: model.CreateSession) -> None:
        events = self.entity.predict_command(command)
        self.create_session(events[0])
        for e in events:
            await self.publish(e)

    @apply.register(UserSignedUp)
    @apply.register(model.UserCreated)
    @classmethod
    def _(cls, event: model.UserCreated) -> ty.Self:
        return cls(user=model.User.apply(event))

    @apply.register(model.SessionCreated)
    @apply.register(model.UserAPIKeyAdded)
    def _(self, event: model.Event) -> ty.Self:
        self.entity.apply(event)
        return self

    @property
    def session_count(self):
        return len(self.entity.session_ids)


class SessionActor(GPTBaseActor["SessionActor", model.ChatSession]):
    def __init__(self, chat_session: model.ChatSession):
        super().__init__(boxfactory=QueueBox, entity=chat_session)

    @property
    def chat_context(self) -> list[model.ChatMessage]:
        return self.entity.messages

    @asynccontextmanager
    async def get_client(self):
        user = self.system.get_child(self.entity.user_id)
        if not user:
            user = await self.system.rebuild_user(self.entity.user_id)

        # TODO: use asyncexitstack
        api_pool = user.get_user_api_pool()
        async with api_pool.lifespan():
            async with api_pool.reserve_client() as client:
                yield client

    async def _send_chatmessage(
        self,
        message: model.ChatMessage,
        model: model.CompletionModels,
        stream: bool = True,
    ) -> ty.AsyncGenerator[str, None]:
        async with self.get_client() as client:
            chunks = await client.send_chat(
                messages=self.chat_context + [message],
                model=model,
                user=self.entity.user_id,
                stream=stream,
            )

        async for resp in chunks:
            for choice in resp.choices:
                content = choice.delta.content
                if not content:
                    continue
                yield content

    async def send_chatmessage(
        self, message: model.ChatMessage, completion_model: model.CompletionModels
    ) -> ty.AsyncGenerator[str, None]:
        "send messages and publish events"
        chunks = self._send_chatmessage(message=message, model=completion_model)
        answer = ""
        async for chunk in chunks:
            answer += chunk
            yield chunk

        message_sent = model.ChatMessageSent(
            session_id=self.entity_id,
            chat_message=message,
        )

        response_received = model.ChatResponseReceived(
            session_id=self.entity_id,
            chat_message=model.ChatMessage(role="assistant", content=answer),
        )

        self.entity.apply(message_sent)
        self.entity.apply(response_received)
        await self.publish(message_sent)
        await self.publish(response_received)

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
        chunks = self._send_chatmessage(
            message=command.chat_message, model=command.model
        )
        message_sent = model.ChatMessageSent(
            session_id=self.entity_id,
            chat_message=command.chat_message,
        )

        answer = await async_receiver(chunks)

        response_received = model.ChatResponseReceived(
            session_id=self.entity_id,
            chat_message=model.ChatMessage(role="assistant", content=answer),
        )

        self.entity.apply(message_sent)
        self.entity.apply(response_received)
        await self.publish(message_sent)
        await self.publish(response_received)

    @singledispatchmethod
    def apply(self, unknown: object) -> ty.Self:
        raise NotImplementedError(f"apply for {unknown} is not implemented")

    @apply.register
    @classmethod
    def _(cls, unknown: object) -> ty.Self:
        raise NotImplementedError(f"apply for {unknown} is not implemented")

    @apply.register
    def _(self, event: model.ChatMessageSent) -> ty.Self:
        self.entity.apply(event)
        return self

    @apply.register
    @classmethod
    def _(cls, event: model.SessionCreated) -> ty.Self:
        return cls(chat_session=model.ChatSession.apply(event))


class GPTSystem(System[UserActor]):
    # TODO: this class should not inherit from system
    # use GPTBaseActor instead
    def __init__(
        self,
        ref: ActorRef,
        settings: Settings,
        boxfactory: BoxFactory,
        cache: cache.Cache[str, str],
    ):
        super().__init__(boxfactory=boxfactory, ref=ref, settings=settings)
        self._system_state = SystemState.created
        self._cache = cache

    @property
    def cache(self) -> cache.Cache[str, str]:
        return self._cache

    @property
    def state(self) -> SystemState:
        return self._system_state

    @state.setter
    def state(self, state: SystemState) -> None:
        if self._system_state is SystemState.stopped:
            raise errors.InvalidStateError("system already stopped")
        self._system_state = state

    async def create_user(self, command: model.CreateUser) -> "UserActor":
        event = model.UserCreated(user_id=command.entity_id)
        user_actor = UserActor.apply(event)
        self.childs[user_actor.entity_id] = user_actor
        await self.publish(event)
        return user_actor

    def setup_journal(
        self, eventstore: eventstore.EventStore, boxfactory: BoxFactory
    ) -> None:
        """
        journal is part of the application layer,
        so it should be created here by gptsystem, not by system actor
        """

        journal_ref = self.settings.actor_refs.JOURNAL
        journal = Journal(eventstore=eventstore, boxfactory=boxfactory, ref=journal_ref)
        self._journal = journal

    async def rebuild_user(self, user_id: str) -> "UserActor":
        events = await self.journal.list_events(user_id)
        if not events:
            raise errors.UserNotRegisteredError(f"No events for user: {user_id}")

        created = events.pop(0)
        user_actor = UserActor.apply(created)
        if events:
            user_actor.rebuild(events)
        self.childs[user_actor.entity_id] = user_actor
        return user_actor

    async def start(self, eventstore: eventstore.EventStore) -> "GPTSystem":
        if self._system_state.is_running:
            raise errors.InvalidStateError("system already started")

        self.setup_journal(eventstore=eventstore, boxfactory=QueueBox)
        self.state = self.state.start()
        return self

    @singledispatchmethod
    def apply(self, event: Event) -> ty.Self:
        raise NotImplementedError

    @singledispatchmethod
    async def handle(self, command: Command) -> None:
        raise NotImplementedError

    @handle.register
    async def _(self, command: model.SendChatMessage) -> None:
        user = self.get_child(command.user_id)
        if not user:
            user = await self.rebuild_user(command.user_id)

        session = user.get_child(command.entity_id)
        if not session:
            session = await user.rebuild_session(command.entity_id)

        await session.handle(command)

    @handle.register
    async def _(self, command: model.CreateUser) -> None:
        await self.create_user(command)

    async def stop(self) -> None:
        logger.info("system stopped")
        self.state = self.state.stop()
