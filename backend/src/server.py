from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI
from src.adapters.factory import adapter_locator
from src.app.api.endpoints import api_router
from src.app.api.error_handlers import HandlerRegistry
from src.app.api.middleware import LoggingMiddleware, TraceMiddleware
from src.app.bootstrap import bootstrap
from src.app.factory import app_service_locator
from src.domain import config
from src.domain._log import logger
from src.infra.factory import event_record_factory


@asynccontextmanager
async def lifespan(app: FastAPI | None = None, *, settings: config.Settings):
    await bootstrap(settings)
    adapters = adapter_locator(settings)
    app_services = app_service_locator(settings)

    event_record = event_record_factory()
    adapters.register(event_record)  # type: ignore

    await app_services.gpt_service.start()

    async with adapters:
        yield

    await app_services.gpt_service.stop()


def add_exception_handlers(app: FastAPI) -> None:
    registry: HandlerRegistry[Exception] = HandlerRegistry()
    for exc, handler in registry:
        app.add_exception_handler(exc, handler)  # type: ignore


def add_middlewares(app: FastAPI) -> None:
    """
    FILO
    """
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TraceMiddleware)


def app_factory(
    lifespan=lifespan,
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
    )

    root_router = APIRouter()
    root_router.include_router(api_router)
    root_router.add_api_route("/health", lambda: "ok", tags=["health check"])

    app.include_router(root_router, prefix=settings.api.API_VERSION_STR)
    add_exception_handlers(app)
    add_middlewares(app)

    logger.success(
        f"server is running at {settings.api.HOST}:{settings.api.PORT}",
        version=f"{settings.api.API_VERSION_STR}",
    )
    return app


def server(settings: config.Settings) -> None:
    import uvicorn

    modulename = settings.get_modulename(__file__)
    uvicorn.run(  # type: ignore
        f"{modulename}:{app_factory.__name__}",
        host=settings.api.HOST,
        port=settings.api.PORT,
        factory=True,
        reload=True,
        reload_excludes=["test_*.py", "conftest.py"],
        log_config=None,
    )


if __name__ == "__main__":
    config.sys_finetune()
    server(config.get_setting("settings.toml"))
