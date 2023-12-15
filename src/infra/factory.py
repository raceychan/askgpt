from functools import lru_cache

from src.domain.config import Settings
from src.domain.interface import IEvent
from src.infra import cache, encrypt, eventstore, mq, sa_utils


def get_async_engine(settings: Settings):
    engine = sa_utils.async_engine_factory(
        db_url=settings.db.ASYNC_DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )

    return engine


def get_engine(settings: Settings):
    engine = sa_utils.engine_factory(
        db_url=settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )
    return engine


@lru_cache(maxsize=1)
def get_eventstore(settings: Settings) -> eventstore.EventStore:
    es = eventstore.EventStore(aioengine=get_async_engine(settings))
    return es


@lru_cache(maxsize=1)
def get_queuebroker(settings: Settings):
    return mq.QueueBroker[IEvent]()


@lru_cache(maxsize=1)
def get_consumer(settings: Settings):
    return mq.BaseConsumer(get_queuebroker(settings))


@lru_cache(maxsize=1)
def get_producer(settings: Settings):
    return mq.BaseProducer(get_queuebroker(settings))


@lru_cache(maxsize=1)
def get_cache(settings: Settings):
    cache_url = settings.redis.URL
    return cache.RedisCache[str, str].build(cache_url)


@lru_cache(maxsize=1)
def get_local_cache(settings: Settings | None = None):
    return cache.MemoryCache[str, str]()


@lru_cache(maxsize=1)
def get_encrypt(settings: Settings):
    return encrypt.Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )


@lru_cache(maxsize=1)
def get_sqldbg(settings: Settings):
    return sa_utils.SQLDebugger(get_engine(settings))
