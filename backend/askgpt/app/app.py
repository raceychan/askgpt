import argparse
import pathlib
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from askgpt.adapters.factory import adapter_locator, make_database  # make_local_cache
from askgpt.app.api import add_exception_handlers, add_middlewares, route_id_factory
from askgpt.app.api.routers import api_router
from askgpt.domain.config import Settings, detect_settings, settings_context
from askgpt.helpers.time import timeout
from askgpt.infra import schema
from askgpt.infra._log import logger, prod_sink, update_sink
from askgpt.infra.factory import event_record_factory


class BoostrapingFailedError(Exception): ...


@timeout(10)
async def bootstrap(settings: Settings):
    async def _prod(settings: Settings):
        update_sink(prod_sink)

    async def _dev(settings: Settings):
        try:
            aiodb = make_database(settings)
            await schema.create_tables(aiodb)
        except Exception as e:
            logger.critical("Failed to bootstrap application")
            raise BoostrapingFailedError(e) from e
        else:
            logger.success(f"db host: {settings.db.HOST}")
            if settings.redis:
                logger.success(f"redis host: {settings.redis.HOST}")

    if settings.is_prod_env:
        await _prod(settings)
    else:
        await _dev(settings)

    adapters = adapter_locator(settings)
    event_record = event_record_factory()
    adapters.register(event_record)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI | None = None):
    settings = settings_context.get()
    await bootstrap(settings)
    async with adapter_locator.singleton:
        yield


def app_factory(
    lifespan=lifespan, start_response=None, *, settings: Settings | None = None
) -> FastAPI:
    settings = settings or detect_settings()
    settings_context.set(settings)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Distributed GPT client built with love",
        version=settings.api.API_VERSION,
        openapi_url=settings.api.OPEN_API,
        docs_url=settings.api.DOCS,
        redoc_url=settings.api.REDOC,
        lifespan=lifespan,
        generate_unique_id_function=route_id_factory,
    )

    root_router = APIRouter()
    root_router.include_router(api_router)
    root_router.add_api_route("/health", lambda: "ok", tags=["health check"])

    app.include_router(root_router, prefix=settings.api.API_VERSION_STR)
    add_exception_handlers(app)
    add_middlewares(app, settings=settings)

    logger.success(
        f"server is running at {settings.api.HOST}:{settings.api.PORT}",
        version=f"{settings.api.API_VERSION_STR}",
    )
    return app
