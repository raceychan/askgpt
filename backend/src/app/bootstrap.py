from functools import partial

from src.adapters.factory import get_database
from src.domain._log import logger, prod_sink, update_sink
from src.domain.config import Settings
from src.infra import schema


async def bootstrap(settings: Settings):
    if settings.is_prod_env:
        update_sink(partial(prod_sink, settings=settings))
        return

    aioengine = get_database(settings)
    await schema.create_tables(aioengine)
    logger.info(f"db: {settings.db.HOST}")
    logger.info(f"redis: {settings.redis.HOST}")
    logger.success("database is ready")
