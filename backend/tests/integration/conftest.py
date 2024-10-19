import datetime
import typing as ty

import pytest
from askgpt.adapters.cache import MemoryCache
from askgpt.adapters.database import AsyncDatabase
from askgpt.adapters.queue import QueueBroker
from askgpt.adapters.uow import UnitOfWork
from askgpt.app.auth.model import UserAuth
from askgpt.app.auth.repository import AuthRepository, UserAuth
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.app.gpt.gptclient import ClientRegistry, OpenAIClient
from askgpt.app.gpt.params import ChatResponse
from askgpt.app.user.repository import UserRepository
from askgpt.app.user.service import UserService
from askgpt.domain.config import Settings
from askgpt.infra.eventstore import EventStore, OutBoxProducer
from askgpt.infra.schema import create_tables
from askgpt.infra.security import Encryptor
from sqlalchemy.ext import asyncio as sa_aio
from tests.conftest import UserDefaults


@pytest.fixture(scope="module")
def aiodb(settings: Settings):
    engine = sa_aio.create_async_engine(
        settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )
    db = AsyncDatabase(engine)
    return db


@pytest.fixture(scope="module")
def uow(aiodb: AsyncDatabase):
    return UnitOfWork(aiodb)


@pytest.fixture(scope="module")
def local_cache():
    return MemoryCache.from_singleton()


@pytest.fixture(scope="module", autouse=True)
async def tables(aiodb: AsyncDatabase):
    await create_tables(aiodb)


@pytest.fixture(scope="module")
async def eventstore(uow: UnitOfWork) -> EventStore:
    es = EventStore(uow)
    return es


@pytest.fixture(scope="module")
def user_auth(test_defaults: UserDefaults):
    return UserAuth(
        credential=test_defaults.USER_INFO,
        last_login=datetime.datetime.utcnow(),
        user_id=test_defaults.USER_ID,
    )


@pytest.fixture(scope="module")
def broker():
    return QueueBroker[ty.Any](100)


@pytest.fixture(scope="module")
def producer(eventstore: EventStore):
    return OutBoxProducer(eventstore)


# @pytest.fixture(scope="module", autouse=True)
# async def redis_cache(settings: Settings):
#     redis = RedisCache[str].build(
#         url=settings.redis.URL,
#         decode_responses=settings.redis.DECODE_RESPONSES,
#         max_connections=settings.redis.MAX_CONNECTIONS,
#         keyspace=settings.redis.keyspaces.APP,
#         socket_timeout=settings.redis.SOCKET_TIMEOUT,
#         socket_connect_timeout=settings.redis.SOCKET_CONNECT_TIMEOUT,
#     )
#     async with redis.lifespan():
#         yield redis


@pytest.fixture(scope="module")
async def event_store(uow: UnitOfWork):
    return EventStore(uow)


@pytest.fixture(scope="module")
async def user_service(uow: UnitOfWork, eventstore: EventStore):
    return UserService(event_store=eventstore, user_repo=UserRepository(uow))


@pytest.fixture(scope="module")
async def auth_service(
    uow: UnitOfWork,
    local_cache: MemoryCache[str, str],
    settings: Settings,
    encryptor: Encryptor,
    eventstore: EventStore,
):
    keyspace = settings.redis.keyspaces.APP.cls_keyspace(TokenRegistry)

    return AuthService(
        auth_repo=AuthRepository(uow),
        encryptor=encryptor,
        token_registry=TokenRegistry(
            token_cache=local_cache,
            keyspace=keyspace,
        ),
        eventstore=eventstore,
        security_settings=settings.security,
    )


@pytest.fixture(scope="module")
async def cache(settings: Settings):
    return MemoryCache()


@pytest.fixture(scope="module")
def chat_response():
    from openai.types.chat import ChatCompletionChunk
    from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

    delta = ChoiceDelta(content="pong")
    choice = Choice(delta=delta, finish_reason="stop", index=0)
    chunk = ChatCompletionChunk(
        id="sth",
        choices=[choice],
        created=0,
        model="model",
        object="chat.completion.chunk",
    )

    return chunk


@pytest.fixture(scope="module", autouse=True)
def openai_client(chat_response: ChatResponse):
    async def asyncgen():
        yield chat_response

    async def asyncresponse():
        return chat_response

    @ClientRegistry.register("askgpt_test")
    class FakeClient(OpenAIClient):
        async def complete(  # type: ignore
            self, **kwargs  # type: ignore
        ):
            assert kwargs["options"].get("stream")
            return asyncgen() if kwargs["options"].get("stream") else asyncresponse()

    return FakeClient.from_apikey("random")
