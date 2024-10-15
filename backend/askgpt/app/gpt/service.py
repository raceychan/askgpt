import typing as ty

from askgpt.adapters.cache import Cache
from askgpt.app.actor import QueueBox as QueueBox
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt.errors import (
    APIKeyNotProvidedError,
    OrphanSessionError,
    SessionNotFoundError,
)
from askgpt.app.gpt.model import (
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
from askgpt.app.gpt.params import ChatGPTRoles
from askgpt.app.gpt.repository import SessionRepository
from askgpt.app.gpt.request import APIPool
from askgpt.app.user.service import UserService
from askgpt.domain.base import SupportedGPTs
from askgpt.domain.config import SETTINGS_CONTEXT
from askgpt.infra.eventstore import EventStore
from askgpt.infra.gptclient import ClientRegistry
from askgpt.infra.security import Encryptor


class GPTService:
    def __init__(
        self,
        encryptor: Encryptor,
        user_service: UserService,
        auth_service: AuthService,
        session_repo: SessionRepository,
        event_store: EventStore,
        cache: Cache[str, str],
    ):
        self._encryptor = encryptor
        self._user_service = user_service
        self._auth_service = auth_service
        self._session_repo = session_repo
        self._event_store = event_store
        self._cache: Cache[str, str] = cache
        #
        self._uow = self._session_repo.uow
        self._settings = SETTINGS_CONTEXT.get()
        self._client_registry = ClientRegistry()

    async def _build_api_pool(self, user_id: str, api_type: str):
        decrypted_api_keys = await self._auth_service.list_api_keys(
            user_id=user_id, api_type=api_type
        )
        if not decrypted_api_keys:
            raise APIKeyNotProvidedError(api_type=api_type)

        pool_keyspace = self._settings.redis.keyspaces.API_POOL / user_id
        user_api_pool = APIPool(
            pool_keyspace=pool_keyspace,
            api_type=api_type,
            api_keys=decrypted_api_keys,
            cache=self._cache,
        )
        return user_api_pool

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

    async def chatcomplete(
        self,
        user_id: str,
        session_id: str,
        gpt_type: SupportedGPTs,
        role: ChatGPTRoles,
        question: str,
        options: dict[str, ty.Any],
    ) -> ty.AsyncGenerator[str, None]:
        session = await self._rebuild_session(user_id=user_id, session_id=session_id)
        api_pool = await self._build_api_pool(user_id=user_id, api_type=gpt_type)
        async with api_pool.reserve_api_key() as api_key:
            client_factory = self._client_registry[gpt_type]
            client = client_factory.from_apikey(api_key)
            message = ChatMessage(role=role, content=question)
            messages = session.messages + [message]
            ans_gen = client.complete(
                messages=messages, model=options.pop("model"), options=options
            )
            answer = ""
            async for chunk in ans_gen:
                yield chunk
                answer += chunk

            events = [
                ChatMessageSent(
                    session_id=session_id,
                    chat_message=message,
                ),
                ChatResponseReceived(
                    session_id=session_id,
                    chat_message=ChatMessage(role="assistant", content=answer),
                ),
            ]
            for e in events:
                session.apply(e)
            await self._event_store.add_all(events)

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
            await self._session_repo.remove(session_id=session_id)
