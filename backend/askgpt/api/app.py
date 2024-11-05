import typing as ty
from contextlib import asynccontextmanager

from askgpt.api.bootstrap import bootstrap
from askgpt.api.error_handlers import handler_registry
from askgpt.api.middleware import middlewares
from askgpt.api.router import feature_router, route_id_factory
from askgpt.domain.config import SETTINGS_CONTEXT, Settings, detect_settings, dg
from askgpt.helpers._log import logger
from askgpt.helpers.error_registry import error_route_factory
from fastapi import APIRouter, FastAPI
from starlette.types import Lifespan


@asynccontextmanager
async def lifespan(app: FastAPI | None = None):
    settings = SETTINGS_CONTEXT.get()
    await bootstrap(settings)
    async with dg:
        yield


def app_factory(
    lifespan: Lifespan[FastAPI] = lifespan,
    start_response: ty.Any = None,
    *,
    settings: Settings | None = None,
) -> FastAPI:
    """app factory that builds the fastapi app instance.
    start_response: gunivorn compatible hook.
    remove this would cause exception in production.
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
