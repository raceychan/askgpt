from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI

# from src.adapters.cache import MemoryCache, RedisCache
from src.adapters.factory import adapter_locator, make_database  # make_local_cache
from src.app.api import route_id_factory
from src.app.api.middleware import add_middlewares
from src.app.api.routers import api_router
from src.domain import config
from src.domain._log import logger, prod_sink, update_sink
from src.domain.config import Settings
from src.helpers.error_handlers import add_exception_handlers
from src.helpers.time import timeout
from src.infra import schema
from src.infra.factory import event_record_factory


class BoostrapingFailedError(Exception): ...


@timeout(10)
async def bootstrap(settings: Settings):
    async def _prod(settings):
        sink = partial(prod_sink, settings=settings)
        update_sink(sink)

    async def _dev(settings):
        try:
            aiodb = make_database(settings)
            await schema.create_tables(aiodb)
        except Exception as e:
            logger.critical("Failed to bootstrap application")
            raise BoostrapingFailedError
        else:
            logger.success(f"db host: {settings.db.HOST}")
            logger.success(f"redis host: {settings.redis.HOST}")

    if settings.is_prod_env:
        await _prod(settings)
    else:
        await _dev(settings)

    adapters = adapter_locator(settings)
    event_record = event_record_factory()
    adapters.register(event_record)  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI | None = None, *, settings: config.Settings):
    await bootstrap(settings)
    async with adapter_locator.singleton:
        yield


def app_factory(
    lifespan=lifespan,  # type: ignore
    *,
    settings: config.Settings = config.get_setting("settings.toml"),
) -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="distributed gpt client built with love",
        version=settings.api.API_VERSION,
        openapi_url=settings.api.OPEN_API,
        docs_url=settings.api.DOCS,
        redoc_url=settings.api.REDOC,
        lifespan=partial(lifespan, settings=settings),  # type: ignore
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