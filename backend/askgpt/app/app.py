from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from askgpt.app.api import add_middlewares, route_id_factory
from askgpt.app.api.error_handlers import add_exception_handlers, handler_registry
from askgpt.app.api.routers import api_router
from askgpt.domain.config import SETTINGS_CONTEXT, Settings, detect_settings
from askgpt.helpers.error_registry import error_route_factory
from askgpt.helpers.time import timeout
from askgpt.infra import schema
from askgpt.infra._log import logger, prod_sink, update_sink
from askgpt.infra.factory import event_listener_factory
from askgpt.infra.locator import adapter_locator, make_database


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
            logger.success(f"db@{settings.db.HOST}:{settings.db.PORT}")
            if settings.redis:
                logger.success(f"redis@{settings.redis.HOST}:{settings.redis.PORT}")

    if settings.is_prod_env:
        await _prod(settings)
    else:
        await _dev(settings)

    adapters = adapter_locator(settings)
    event_listener = event_listener_factory()
    adapters.register_context(event_listener)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI | None = None):
    settings = SETTINGS_CONTEXT.get()
    await bootstrap(settings)
    async with adapter_locator.singleton:
        yield


def app_factory(
    lifespan=lifespan, start_response=None, *, settings: Settings | None = None
) -> FastAPI:
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
    )

    error_route = error_route_factory(handler_registry, route_path="/errors")

    root_router = APIRouter(prefix=settings.api.API_VERSION_STR)
    root_router.include_router(api_router)
    root_router.include_router(error_route)
    root_router.add_api_route("/health", lambda: "ok", tags=["health check"])

    app.include_router(root_router)
    add_exception_handlers(app)
    add_middlewares(app, settings=settings)

    logger.success(
        f"server is running at {settings.api.HOST}:{settings.api.PORT}",
        version=f"{settings.api.API_VERSION_STR}",
    )
    return app
