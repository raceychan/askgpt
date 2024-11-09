from askgpt.adapters.cache import Cache, RedisCache
from askgpt.adapters.database import AsyncDatabase
from askgpt.app.auth._repository import AuthRepository
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.domain.config import Settings, dg
from askgpt.helpers.functions import simplecache
from askgpt.helpers.sql import IEngine, UnitOfWork, async_engine, engine_factory
from askgpt.infra.eventstore import EventStore
from askgpt.infra.security import Encryptor


def make_engine(settings: Settings):
    connect_args = (
        settings.db.connect_args.model_dump() if settings.db.connect_args else None
    )
    execution_options = (
        settings.db.execution_options.model_dump()
        if settings.db.execution_options
        else None
    )
    engine = engine_factory(
        db_url=settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
        connect_args=connect_args,
        execution_options=execution_options,
    )
    return engine


@simplecache
def make_async_engine(settings: Settings):
    async_engine_ = async_engine(make_engine(settings))
    return async_engine_


@dg.node
def database_factory(settings: Settings) -> IEngine:
    return AsyncDatabase(make_async_engine(settings))


@dg.node
def cache_facotry(settings: Settings) -> Cache[str, str]:
    config = settings.redis
    return RedisCache[str].build(
        url=config.URL,
        keyspace=config.keyspaces.APP,
        socket_timeout=config.SOCKET_TIMEOUT,
        decode_responses=config.DECODE_RESPONSES,
        max_connections=config.MAX_CONNECTIONS,
        socket_connect_timeout=config.SOCKET_CONNECT_TIMEOUT,
    )


@simplecache
@dg.node
def uow_factory(settings: Settings) -> UnitOfWork:
    return UnitOfWork(database_factory(settings))


@dg.node
def encrypt_facotry(settings: Settings) -> Encryptor:
    encrypt = Encryptor(
        secret_key=settings.security.SECRET_KEY.get_secret_value(),
        algorithm=settings.security.ALGORITHM,  # type: ignore
    )
    return encrypt


@dg.node
def auth_service_factory(
    settings: Settings,
    auth_repo: AuthRepository,
    token_registry: TokenRegistry,
    encryptor: Encryptor,
    eventstore: EventStore,
) -> AuthService:
    auth_service = AuthService(
        auth_repo=auth_repo,
        token_registry=token_registry,
        encryptor=encryptor,
        eventstore=eventstore,
        security_settings=settings.security,
    )
    return auth_service


