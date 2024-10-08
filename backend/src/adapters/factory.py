import typing as ty
from functools import partial

from src.adapters import cache, database, gptclient, queue, tokenbucket
from src.domain.config import Settings, settingfactory
from src.domain.interface import IEvent
from src.helpers import sql
from src.infra import eventstore
from src.infra.service_locator import Dependency, InfraLocator


@settingfactory
def make_async_engine(settings: Settings):
    async_engine = sql.asyncengine(make_engine(settings))
    return async_engine


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
    engine = sql.engine_factory(
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
def make_eventstore(settings: Settings) -> eventstore.EventStore:
    es = eventstore.EventStore(aiodb=make_database(settings))
    return es


@settingfactory
def make_broker(settings: Settings):
    return queue.QueueBroker[IEvent]()


@settingfactory
def make_consumer(settings: Settings):
    return queue.BaseConsumer(make_broker(settings))


@settingfactory
def make_producer(settings: Settings):
    return queue.BaseProducer(make_broker(settings))


@settingfactory
def make_cache(settings: Settings):
    config = settings.redis
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
    return sql.SQLDebugger(make_engine(settings))


def make_request_client(settings: Settings):
    configs = settings.openai_client
    return partial(
        gptclient.OpenAIClient.build,
        timeout=configs.TIMEOUT,
        max_retries=configs.MAX_RETRIES,
    )


class adapter_locator(InfraLocator):
    # aiodb: Dependency[database.AsyncDatabase]
    aiodb = Dependency(database.AsyncDatabase, make_database)
    redis_cache = Dependency(cache.RedisCache[str], make_cache)
    consumer = Dependency(queue.BaseConsumer[ty.Any], make_consumer)
    producer = Dependency(queue.BaseProducer[ty.Any], make_producer)

    @classmethod
    def build_token_bucket(cls, keyspace: cache.KeySpace):
        script = cls.settings.redis.TOKEN_BUCKET_SCRIPT
        script_func = cls.redis_cache.load_script(script)
        return tokenbucket.TokenBucketFactory(
            redis=cls.redis_cache,
            script=script_func,
            keyspace=keyspace,
        )
