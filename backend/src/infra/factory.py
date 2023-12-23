from src.domain.config import Settings, settingfactory
from src.domain.interface import IEvent
from src.infra import cache, encrypt, eventstore, mq, sa_utils


def get_async_engine(settings: Settings):
    return sa_utils.asyncengine(get_engine(settings))


def get_engine(settings: Settings):
    engine = sa_utils.engine_factory(
        db_url=settings.db.DB_URL,
        echo=settings.db.ENGINE_ECHO,
        isolation_level=settings.db.ISOLATION_LEVEL,
        pool_pre_ping=True,
        connect_args=settings.db.connect_args.model_dump(),
        execution_options=settings.db.execution_options.model_dump(),
    )
    return engine


@settingfactory
def get_eventstore(settings: Settings) -> eventstore.EventStore:
    es = eventstore.EventStore(aioengine=get_async_engine(settings))
    return es


@settingfactory
def get_queuebroker(settings: Settings):
    return mq.QueueBroker[IEvent]()


@settingfactory
def get_consumer(settings: Settings):
    return mq.BaseConsumer(get_queuebroker(settings))


@settingfactory
def get_producer(settings: Settings):
    return mq.BaseProducer(get_queuebroker(settings))


@settingfactory
def get_cache(settings: Settings):
    cache_url = settings.redis.URL
    return cache.RedisCache.build(cache_url)


@settingfactory
def get_local_cache(settings: Settings | None = None):
    return cache.MemoryCache[str, str]()


@settingfactory
def get_encrypt(settings: Settings):
    return encrypt.Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )


@settingfactory
def get_sqldbg(settings: Settings):
    return sa_utils.SQLDebugger(get_engine(settings))
