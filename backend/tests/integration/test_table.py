from sqlalchemy.ext import asyncio as sa_aio


async def test_table_exist(async_engine: sa_aio.AsyncEngine):
    import sqlalchemy as sa
    from sqlalchemy.ext import asyncio as sa_aio

    engine: sa_aio.AsyncEngine = async_engine

    sql = "SELECT name FROM sqlite_schema WHERE type='table' and name='domain_events' ORDER BY name"

    async with engine.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        result = cache.one()
    assert "domain_events" in result
