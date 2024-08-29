from functools import partial

from src.adapters.factory import make_database
from src.domain._log import logger, prod_sink, update_sink
from src.domain.config import Settings
from src.infra import schema


async def bootstrap(settings: Settings):
    try:
        if settings.is_prod_env:
            update_sink(partial(prod_sink, settings=settings))
            return

        aioengine = make_database(settings)
        await schema.create_tables(aioengine)
    except Exception as e:
        logger.error("Failed to bootstrap application")
        raise e
    else:
        logger.info(f"db: {settings.db.HOST}")
        logger.info(f"redis: {settings.redis.HOST}")
        logger.success("database is ready")

