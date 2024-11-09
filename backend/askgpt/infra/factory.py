import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

from askgpt.adapters import database
from askgpt.domain.config import Settings, settingfactory
from askgpt.helpers.sql import async_engine, engine_factory


@settingfactory
def make_async_engine(settings: Settings) -> sa_aio.AsyncEngine:
    async_engine_ = async_engine(make_engine(settings))
    return async_engine_


@settingfactory
def make_engine(settings: Settings) -> sa.Engine:
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


@settingfactory
def make_database(settings: Settings) -> database.AsyncDatabase:
    return database.AsyncDatabase(make_async_engine(settings))


# @settingfactory
# def make_cache(settings: Settings) -> cache.RedisCache[str]:
#     config = settings.redis
#     if not config:
#         raise MissingConfigError(Settings.Redis)
#     return cache.RedisCache[str].build(
#         url=config.URL,
#         keyspace=config.keyspaces.APP,
#         socket_timeout=config.SOCKET_TIMEOUT,
#         decode_responses=config.DECODE_RESPONSES,
#         max_connections=config.MAX_CONNECTIONS,
#         socket_connect_timeout=config.SOCKET_CONNECT_TIMEOUT,
#     )


# @settingfactory
# def make_local_cache(settings: Settings) -> cache.MemoryCache[str, str]:
#     return cache.MemoryCache[str, str]()


# @settingfactory
# def make_sqldbg(settings: Settings) -> SQLDebugger:
#     return SQLDebugger(make_engine(settings))
