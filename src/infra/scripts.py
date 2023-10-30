import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

from infra.sa_utils import engine_factory
from infra.schema import EventSchema


async def test_table_exists(table_name: str, async_engine: sa_aio.AsyncEngine):
    sql = f"SELECT name FROM sqlite_schema WHERE type='table' and name='{table_name}' ORDER BY name"
    async with async_engine.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        result = cache.one_or_none()

    if result != table_name:
        raise ValueError(f"Table {table_name} does not exist")


async def create_eventstore(async_engine: sa_aio.AsyncEngine):
    await EventSchema.create_table_async(async_engine)


async def setup_eventstore(settings):
    if settings.db.DB_DRIVER == "sqlite":
        if not settings.db.DATABASE.exists():
            raise FileNotFoundError(
                f"Database file not found at {settings.db.DATABASE}"
            )

    engine = engine_factory(settings.db.ASYNC_DB_URL, isolation_level="SERIALIZABLE")

    try:
        await test_table_exists(EventSchema.__tablename__, engine)
    except ValueError:
        await create_eventstore(engine)
