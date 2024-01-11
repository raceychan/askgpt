from src.domain._log import logger, prod_sink, update_sink
from src.domain.config import Settings
from src.infra import factory, schema


async def bootstrap(settings: Settings):
    if settings.is_prod_env:
        update_sink(prod_sink)
        return

    aioengine = factory.get_async_engine(settings)
    await schema.create_tables(aioengine)
    logger.success("database is ready")
