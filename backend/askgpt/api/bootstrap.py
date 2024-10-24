import asyncio
import typing as ty

import httpx

from askgpt.adapters.request import client_factory
from askgpt.domain.config import Settings
from askgpt.domain.errors import BoostrapingFailedError
from askgpt.helpers._log import logger, prod_sink, update_sink
from askgpt.helpers.time import timeout
from askgpt.infra.locator import adapter_locator, make_database
from askgpt.infra.schema import create_tables

__all__ = ["bootstrap"]


async def _check_endpoint_available(client: httpx.AsyncClient, url: str):
    try:
        resp = await client.get(url, timeout=3.0)
        assert resp.status_code in (200, 421)
    except Exception as e:
        raise BoostrapingFailedError(
            f"Failed to connect to {url}, check your network"
        ) from e


async def _check_dependencies_available(settings: Settings):
    """
    Check if all dependencies are available.
    may or may not be fatal.
    """
    client = client_factory()

    tasks: list[asyncio.Task[ty.Any]] = []
    for url in settings.api.DEPENDENCIES_CHECK_URL:
        task = asyncio.create_task(_check_endpoint_available(client, url))
        tasks.append(task)

    _, pending = await asyncio.wait(
        *tasks, return_when=asyncio.ALL_COMPLETED, timeout=settings.BOOTSTRAP_TIMEOUT
    )
    if not pending:
        return

    for task in pending:
        if not task.exception():
            continue
        exc = task.exception()
        raise BoostrapingFailedError(
            f"Failed to connect to {task.args[0]}, {exc} check your network"
        ) from exc


async def _prod_bootstrap(settings: Settings):
    update_sink(prod_sink)


async def _dev_bootstrap(settings: Settings):
    try:
        aiodb = make_database(settings)
        await create_tables(aiodb)
    except Exception as e:
        logger.exception("Failed to bootstrap application")
        raise BoostrapingFailedError(e) from e

    logger.debug(f"db@{settings.db.HOST}:{settings.db.PORT}:{settings.db.DATABASE}")
    if settings.redis:
        logger.debug(f"redis@{settings.redis.HOST}:{settings.redis.PORT}")


@timeout(30, logger=logger)
async def bootstrap(settings: Settings):

    logger.info(f"Applying {settings.CONFIG_FILE_NAME}")
    logger.info(f"{settings.PROJECT_NAME} is running in <{settings.RUNTIME_ENV}> env")

    await _check_dependencies_available(settings)

    if settings.is_prod_env:
        await _prod_bootstrap(settings)
    else:
        await _dev_bootstrap(settings)

    adapter_locator.build_singleton(settings)

    logger.info("Application startup complete.")
