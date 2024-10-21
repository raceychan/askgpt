import abc
import typing as ty

from askgpt.adapters.cache import Cache
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt._api_pool import APIPool
from askgpt.app.gpt._errors import (
    APIKeyNotProvidedError,
    OrphanSessionError,
    SessionNotFoundError,
)
from askgpt.app.gpt._gptclient import AnthropicClient, GPTClient, OpenAIClient
from askgpt.app.gpt._model import (
    DEFAULT_SESSION_NAME,
    ChatMessage,
    ChatMessageSent,
    ChatResponseReceived,
    ChatSession,
    SessionCreated,
    SessionRemoved,
    SessionRenamed,
    uuid_factory,
)
from askgpt.app.gpt._repository import SessionRepository
from askgpt.app.gpt.anthropic import _params as anthropic_params
from askgpt.app.gpt.openai import _params as openai_params
from askgpt.domain.config import SETTINGS_CONTEXT
from askgpt.domain.types import SupportedGPTs
from askgpt.infra.eventstore import EventStore


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        event_store: EventStore,
    ):
        self._uow = session_repo.uow
        self._session_repo = session_repo
        self._event_store = event_store

    async def _rebuild_session(self, user_id: str, session_id: str) -> ChatSession:
        async with self._uow.trans():
            user_events = await self._event_store.get(entity_id=user_id)
            for e in user_events:
                if type(e) is SessionCreated:
                    break
            else:
                raise SessionNotFoundError(session_id)

            session = ChatSession.apply(e)
            if user_id != session.user_id:
                raise OrphanSessionError(session_id, user_id)
            session_events = await self._event_store.get(entity_id=session_id)
            for event in session_events:
                session.apply(event)
            return session

    async def create_session(
        self, user_id: str, session_name: str = DEFAULT_SESSION_NAME
    ) -> ChatSession:
        session_id = uuid_factory()
        ss = ChatSession(
            user_id=user_id, session_id=session_id, session_name=session_name
        )
        event = SessionCreated(
            session_id=session_id, user_id=user_id, session_name=session_name
        )
        ss.apply(event)

        async with self._uow.trans():
            await self._session_repo.add(ss)
            await self._event_store.add(event)
        return ss

    async def get_session(self, user_id: str, session_id: str) -> ChatSession:
        async with self._uow.trans():
            session = await self._rebuild_session(
                user_id=user_id, session_id=session_id
            )
        return session

    async def list_sessions(self, user_id: str) -> list[ChatSession]:
        async with self._uow.trans():
            sessions = await self._session_repo.list_sessions(user_id=user_id)
        return sessions

    async def rename_session(self, session_id: str, new_name: str) -> None:
        async with self._uow.trans():
            chat_session = await self._session_repo.get(entity_id=session_id)
            if not chat_session:
                raise SessionNotFoundError(session_id)
            if chat_session.session_name == new_name:
                return
            session_renamed = SessionRenamed(session_id=session_id, new_name=new_name)
            chat_session.apply(session_renamed)
            await self._event_store.add(session_renamed)
            await self._session_repo.rename(chat_session)

    async def delete_session(self, session_id: str) -> None:
        session_removed = SessionRemoved(session_id=session_id)
        async with self._uow.trans():
            await self._event_store.add(session_removed)
            await self._session_repo.remove(entity_id=session_id)


class GPTService:
    gpt_type: ty.ClassVar[SupportedGPTs]

    def __init__(
        self,
        auth_service: AuthService,
        session_service: SessionService,
        event_store: EventStore,
        cache: Cache[str, str],
    ):
        self._auth_service = auth_service
        self._session_service = session_service
        self._cache = cache
        self._event_store = event_store
        self._settings = SETTINGS_CONTEXT.get()

    async def _build_api_pool(self, user_id: str, api_type: str):
        decrypted_api_keys = await self._auth_service.list_api_keys(
            user_id=user_id, api_type=api_type, as_secret=False
        )
        if not decrypted_api_keys:
            raise APIKeyNotProvidedError(api_type=api_type)

        pool_keyspace = self._settings.redis.keyspaces.API_POOL / user_id
        user_api_pool = APIPool(
            pool_keyspace=pool_keyspace,
            api_type=api_type,
            api_keys=tuple(key for _, _, key in decrypted_api_keys),
            cache=self._cache,
        )
        return user_api_pool

    @abc.abstractmethod
    def _message_adapter(self, messages: list[ChatMessage]):
        """
        Adapt messages to the format expected by the API
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _client_factory(self, api_key: str, timeout: float) -> "GPTClient":
        raise NotImplementedError

    async def build_message_context(
        self, session: ChatSession, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        messages = session.messages + messages
        return self._message_adapter(messages)

    async def chatcomplete(
        self,
        user_id: str,
        session_id: str,
        params: (
            openai_params.OpenAIChatMessageOptions
            | anthropic_params.AnthropicChatMessageOptions
        ),
    ) -> ty.AsyncGenerator[str, None]:
        session = await self._session_service._rebuild_session(
            user_id=user_id, session_id=session_id
        )
        raw_message = params.pop("messages", [])
        message = raw_message[0]

        msg = ChatMessage(
            role=message["role"], content=message["content"], gpt_type=self.gpt_type
        )
        messages = await self.build_message_context(session, messages=[msg])
        api_pool = await self._build_api_pool(user_id=user_id, api_type=self.gpt_type)
        async with api_pool.reserve_api_key() as api_key:
            client = self._client_factory(api_key, timeout=3.0)
            answer = ""
            async for chunk in client.complete(messages=messages, params=params):
                yield chunk
                answer += chunk

        events = [
            ChatMessageSent(
                session_id=session_id,
                chat_message=msg,
            ),
            ChatResponseReceived(
                session_id=session_id,
                chat_message=ChatMessage(
                    role="assistant", content=answer, gpt_type=self.gpt_type
                ),
            ),
        ]
        for e in events:
            session.apply(e)

        # TODO: extract this to be an event serivce
        # await self._event_service.publish(events)
        async with self._session_service._session_repo.uow.trans():
            await self._event_store.add_all(events)


class OpenAIGPT(GPTService):
    gpt_type: ty.ClassVar[SupportedGPTs] = "openai"

    def _message_adapter(
        self, messages: list[ChatMessage]
    ) -> list[openai_params.ChatCompletionMessageParam]:
        adapted = ty.cast(
            list[openai_params.ChatCompletionMessageParam],
            [dict(content=message.content, role=message.role) for message in messages],
        )
        return adapted

    def _client_factory(self, api_key: str, timeout: float) -> OpenAIClient:
        return OpenAIClient.from_apikey(api_key, timeout=timeout)


class AnthropicGPT(GPTService):
    gpt_type: ty.ClassVar[SupportedGPTs] = "anthropic"

    def _message_adapter(
        self, messages: list[ChatMessage]
    ) -> list[anthropic_params.MessageParam]:
        return [
            anthropic_params.MessageParam(
                content=message.content,
                role="user" if message.role in ("system", "user") else "assistant",
            )
            for message in messages
        ]

    def _client_factory(self, api_key: str, timeout: float) -> AnthropicClient:
        return AnthropicClient.from_apikey(api_key, timeout=timeout)
