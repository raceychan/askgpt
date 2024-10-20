import typing as ty

from askgpt.adapters import cache, database, tokenbucket
from askgpt.domain.config import MissingConfigError, Settings, settingfactory
from askgpt.helpers.sdb import SQLDebugger
from askgpt.helpers.service_locator import Dependency, InfraLocator
from askgpt.helpers.sql import async_engine, engine_factory


@settingfactory
def make_async_engine(settings: Settings):
    async_engine_ = async_engine(make_engine(settings))
    return async_engine_


@settingfactory
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


@settingfactory
def make_database(settings: Settings) -> database.AsyncDatabase:
    return database.AsyncDatabase(make_async_engine(settings))


@settingfactory
def make_cache(settings: Settings):
    config = settings.redis
    if not config:
        raise MissingConfigError(Settings.Redis)
    return cache.RedisCache[str].build(
        url=config.URL,
        keyspace=config.keyspaces.APP,
        socket_timeout=config.SOCKET_TIMEOUT,
        decode_responses=config.DECODE_RESPONSES,
        max_connections=config.MAX_CONNECTIONS,
        socket_connect_timeout=config.SOCKET_CONNECT_TIMEOUT,
    )


@settingfactory
def make_local_cache(settings: Settings):
    return cache.MemoryCache[str, str]()


@settingfactory
def make_sqldbg(settings: Settings):
    return SQLDebugger(make_engine(settings))


class adapter_locator(InfraLocator):
    # should be a global context var with resource management
    aiodb = Dependency(database.AsyncDatabase, make_database)
    aiocache = Dependency(cache.RedisCache[str], make_cache)

    @classmethod
    def build_token_bucket(cls, keyspace: cache.KeySpace):
        if not cls.settings.redis:
            raise MissingConfigError(Settings.Redis)
        script = cls.settings.redis.TOKEN_BUCKET_SCRIPT
        script_func = cls.aiocache.load_script(script)
        return tokenbucket.TokenBucketFactory(
            redis=cls.aiocache,
            script=script_func,
            keyspace=keyspace,
        )

    @classmethod
    def build_singleton(cls, settings: Settings) -> ty.Self:
        return cls(settings)
