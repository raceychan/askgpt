import typing as ty
from contextlib import asynccontextmanager

from askgpt.adapters.request import client_factory
from askgpt.api.error_handlers import handler_registry
from askgpt.api.middleware import middlewares
from askgpt.api.router import feature_router, route_id_factory
from askgpt.domain.config import SETTINGS_CONTEXT, Settings, detect_settings
from askgpt.domain.errors import BoostrapingFailedError
from askgpt.helpers._log import logger, prod_sink, update_sink
from askgpt.helpers.error_registry import error_route_factory
from askgpt.helpers.time import timeout
from askgpt.infra.locator import adapter_locator, make_database
from askgpt.infra.schema import create_tables
from fastapi import APIRouter, FastAPI
from starlette.types import Lifespan


async def check_openai_endpoint(settings: Settings):
    url = "https://api.openai.com"
    client = client_factory()
    try:
        resp = await client.get(url, timeout=3.0)
        assert resp.status_code in (200, 421)
    except Exception as e:
        raise BoostrapingFailedError(
            "Failed to connect to openai endpoint, check your network"
        ) from e


@timeout(30, logger=logger)
async def bootstrap(settings: Settings):
    # TODO: need to check openai endpoint availability here!
    async def _prod(settings: Settings):
        update_sink(prod_sink)

    async def _dev(settings: Settings):
        try:
            aiodb = make_database(settings)
            await create_tables(aiodb)
        except Exception as e:
            logger.exception("Failed to bootstrap application")
            raise BoostrapingFailedError(e) from e

        logger.debug(f"db@{settings.db.HOST}:{settings.db.PORT}:{settings.db.DATABASE}")
        if settings.redis:
            logger.debug(f"redis@{settings.redis.HOST}:{settings.redis.PORT}")

    logger.info(f"Applying {settings.FILE_NAME}")
    logger.info(f"{settings.PROJECT_NAME} is running in <{settings.RUNTIME_ENV}> env")

    await check_openai_endpoint(settings)
    if settings.is_prod_env:
        await _prod(settings)
    else:
        await _dev(settings)

    adapter_locator.build_singleton(settings)

    logger.info("Application startup complete.")


@asynccontextmanager
async def lifespan(app: FastAPI | None = None):
    settings = SETTINGS_CONTEXT.get()
    await bootstrap(settings)
    async with adapter_locator.singleton:
        yield


def app_factory(
    lifespan: Lifespan[FastAPI] = lifespan,
    start_response: ty.Any = None,
    *,
    settings: Settings | None = None,
) -> FastAPI:
    """app factory that builds the fastapi app instance.
    start_response: gunivorn compatible hook.
    """
    settings = settings or detect_settings()
    SETTINGS_CONTEXT.set(settings)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Distributed GPT client built with love",
        version=settings.api.API_VERSION,
        openapi_url=settings.api.OPEN_API,
        docs_url=settings.api.DOCS,
        redoc_url=settings.api.REDOC,
        lifespan=lifespan,
        generate_unique_id_function=route_id_factory,
        middleware=middlewares(settings=settings),
        exception_handlers=handler_registry.handlers,
    )

    error_route = error_route_factory(handler_registry, route_path="/errors")

    root_router = APIRouter(prefix=settings.api.API_VERSION_STR)
    root_router.include_router(feature_router)
    root_router.include_router(error_route)
    app.include_router(root_router)

    logger.success(
        f"server is running at {settings.api.HOST}:{settings.api.PORT}",
        version=f"{settings.api.API_VERSION_STR}",
    )
    return app
