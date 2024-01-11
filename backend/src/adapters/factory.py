from src.adapters import cache, database, queue, tokenbucket
from src.domain.config import Settings
from src.domain.interface import IEvent
from src.infra import eventstore
from src.infra.service_registry import Dependency, InfraRegistryBase
from src.toolkit import sa_utils


def get_async_engine(settings: Settings):
    async_engine = sa_utils.asyncengine(get_engine(settings))
    return async_engine


def get_engine(settings: Settings):
    engine = sa_utils.engine_factory(
        db_url=settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
        connect_args=settings.db.connect_args,
        execution_options=settings.db.execution_options.model_dump(),
    )
    return engine


def get_database(settings: Settings) -> database.AsyncDatabase:
    return database.AsyncDatabase(get_async_engine(settings))


def get_eventstore(settings: Settings) -> eventstore.EventStore:
    es = eventstore.EventStore(aioengine=get_async_engine(settings))
    return es


def get_queuebroker(settings: Settings):
    # TODO: return different broker based on settings
    return queue.QueueBroker[IEvent]()


def get_consumer(settings: Settings):
    return queue.BaseConsumer(get_queuebroker(settings))


def get_producer(settings: Settings):
    return queue.BaseProducer(get_queuebroker(settings))


def get_cache(settings: Settings):
    config = settings.redis
    return cache.RedisCache.build(
        url=config.URL,
        keyspace=config.keyspaces.APP,
        socket_timeout=config.SOCKET_TIMEOUT,
        decode_responses=config.DECODE_RESPONSES,
        max_connections=config.MAX_CONNECTIONS,
        socket_connect_timeout=config.SOCKET_CONNECT_TIMEOUT,
    )


def get_local_cache(settings: Settings):
    return cache.MemoryCache[str, str]()


def get_sqldbg(settings: Settings):
    return sa_utils.SQLDebugger(get_engine(settings))


def get_tokenbucket_factory(settings: Settings, keyspace: cache.KeySpace):
    redis = get_cache(settings)
    script = settings.redis.TOKEN_BUCKET_SCRIPT
    script_func = redis.load_script(script)
    return tokenbucket.TokenBucketFactory(
        redis=redis,
        script=script_func,
        keyspace=keyspace,
    )


class AdapterRegistry(InfraRegistryBase):
    database = Dependency(database.AsyncDatabase, get_database)
    cache = Dependency(cache.RedisCache, get_cache)
