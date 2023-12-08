from functools import lru_cache

from src.domain.config import Settings
from src.domain.interface import IEvent
from src.infra.eventstore import EventStore
from src.infra.mq import BaseConsumer, BaseProducer, QueueBroker
from src.infra.sa_utils import async_engine_factory, engine_factory


# pre-configs factories
def get_async_engine(settings: Settings):
    engine = async_engine_factory(
        db_url=settings.db.ASYNC_DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )
    return engine


def get_engine(settings: Settings):
    engine = engine_factory(
        db_url=settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
    )
    return engine


@lru_cache(maxsize=1)
def get_eventstore(settings: Settings):
    es = EventStore(aioengine=get_async_engine(settings))
    return es


@lru_cache(maxsize=1)
def get_broker(settings: Settings):
    return QueueBroker[IEvent]()


@lru_cache(maxsize=1)
def get_consumer(settings: Settings):
    return BaseConsumer(get_broker(settings))


@lru_cache(maxsize=1)
def get_producer(settings: Settings):
    return BaseProducer(get_broker(settings))
