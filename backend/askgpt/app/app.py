import argparse
import pathlib
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI

from askgpt.adapters.factory import adapter_locator, make_database  # make_local_cache
from askgpt.app.api import route_id_factory
from askgpt.app.api.middleware import add_middlewares
from askgpt.app.api.routers import api_router
from askgpt.domain import config
from askgpt.domain._log import logger, prod_sink, update_sink
from askgpt.domain.config import Settings
from askgpt.helpers.error_handlers import add_exception_handlers
from askgpt.helpers.time import timeout
from askgpt.infra import schema
from askgpt.infra.factory import event_record_factory


def parser_factory() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="store")
    return parser


class Options(argparse.Namespace):
    config_path: pathlib.Path = pathlib.Path("askgpt/dev.settings.toml")

    @classmethod
    def parse(cls, parser: argparse.ArgumentParser):
        return parser.parse_args(namespace=cls)


def get_ops():
    return Options.parse(parser_factory())


class BoostrapingFailedError(Exception):
    ...


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
async def lifespan(app: FastAPI | None = None, *, settings: config.Settings):
    await bootstrap(settings)
    async with adapter_locator.singleton:
        yield


def app_factory(
    lifespan=lifespan, *, settings: config.Settings | None = None
) -> FastAPI:
    ops = get_ops()
    settings = config.get_setting(ops.config_path)
    config.settings_context.set(settings)
    # settings = settings or config.settings_context.get()
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
