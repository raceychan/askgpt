import pytest

from src.infra.eventstore import EventStore
from src.infra.schema import EventSchema


@pytest.fixture(scope="module")
def async_engine(settings):
    from sqlalchemy.ext import asyncio as sa_aio

    engine = sa_aio.create_async_engine(
        settings.db.ASYNC_DB_URL, echo=settings.db.ENGINE_ECHO, pool_pre_ping=True
    )
    return engine


@pytest.fixture(scope="module", autouse=True)
async def event_table(async_engine):
    await EventSchema.create_table_async(async_engine)


@pytest.fixture(scope="module")
async def eventstore(async_engine) -> EventStore:
    es = EventStore(async_engine)
    return es


async def test_table_exist(async_engine):
    import sqlalchemy as sa
    from sqlalchemy.ext import asyncio as sa_aio

    engine: sa_aio.AsyncEngine = async_engine

    sql = "SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"

    async with engine.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        result = cache.one()
    assert "domain_events" in result._tuple()
