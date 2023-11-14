import pytest
from sqlalchemy.ext import asyncio as sa_aio

from src.domain.interface import ISettings
from src.infra.eventstore import EventStore
from src.infra.schema import EventSchema


@pytest.fixture(scope="module")
def async_engine(settings: ISettings):
    engine = sa_aio.create_async_engine(
        settings.db.ASYNC_DB_URL,
        echo=settings.db.ENGINE_ECHO,
        pool_pre_ping=True,
        isolation_level=settings.db.ISOLATION_LEVEL,
    )
    return engine


@pytest.fixture(scope="module", autouse=True)
async def event_table(async_engine: sa_aio.AsyncEngine):
    await EventSchema.create_table_async(async_engine)
    await EventSchema.assure_table_exist(async_engine)


@pytest.fixture(scope="module")
async def eventstore(async_engine: sa_aio.AsyncEngine) -> EventStore:
    es = EventStore(async_engine)
    return es
