from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import APIRouter, FastAPI
from src.app.api.error_handlers import HandlerRegistry
from src.app.api.middleware import LoggingMiddleware, TraceMiddleware
from src.app.api.router import api_router
from src.app.bootstrap import bootstrap
from src.app.factory import ApplicationServices
from src.domain._log import logger
from src.domain.config import Settings, get_setting

stack = AsyncExitStack()

# TODO: implement container to store dependencies
# reff: https://python-dependency-injector.ets-labs.org/examples/fastapi-sqlalchemy.html


@asynccontextmanager
async def lifespan(app: FastAPI, settings: Settings = get_setting()):
    await bootstrap(settings)
    async with ApplicationServices(settings) as registry:
        yield


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
    # TODO: add throttling middleware


def app_factory(*, lifespan=lifespan, settings=get_setting("settings.toml")) -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="gpt service at your home",
        version=settings.api.API_VERSION,
        openapi_url=settings.api.OPEN_API,
        docs_url=settings.api.DOCS,
        redoc_url=settings.api.REDOC,
        lifespan=lifespan,
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


def server(settings: Settings) -> None:
    import uvicorn

    modulename = settings.get_modulename(__file__)
    uvicorn.run(  # type: ignore
        f"{modulename}:app_factory",
        host=settings.api.HOST,
        port=settings.api.PORT,
        factory=True,
        reload=True,
        reload_excludes=["test_*.py", "conftest.py"],
        log_config=None,
    )


if __name__ == "__main__":
    server(get_setting("settings.toml"))