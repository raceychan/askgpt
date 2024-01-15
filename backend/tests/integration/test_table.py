from src.adapters.database import AsyncDatabase


async def test_table_exist(aiodb: AsyncDatabase):
    import sqlalchemy as sa

    sql = "SELECT name FROM sqlite_schema WHERE type='table' and name='domain_events' ORDER BY name"

    async with aiodb.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        result = cache.one()
    assert "domain_events" in result
