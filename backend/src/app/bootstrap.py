from src.domain.config import Settings
from src.infra import factory, schema


async def bootstrap(settings: Settings):
    aioengine = factory.get_async_engine(settings)
    await schema.create_tables(aioengine)
