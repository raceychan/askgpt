from src.domain.config import Settings
from src.infra.sa_utils import async_engine_factory, engine_factory


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
