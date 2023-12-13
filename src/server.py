from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI

from src.app.api.error_handlers import HandlerRegistry
from src.app.api.middleware import LoggingMiddleware, TraceMiddleware
from src.app.api.router import api_router
from src.app.bootstrap import bootstrap
from src.app.factory import get_eventrecord
from src.domain._log import logger
from src.domain.config import get_setting
from src.infra.factory import get_async_engine

stack = AsyncExitStack()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_setting()
    engine = get_async_engine(settings)
    await bootstrap(engine)
    record = get_eventrecord(settings)

    async with stack:
        await stack.enter_async_context(record.lifespan())
        yield

    # await engine.dispose()


def add_exception_handlers(app: FastAPI):
    registry: HandlerRegistry[Exception] = HandlerRegistry()
    for exc, handler in registry:
        app.add_exception_handler(exc, handler)  # type: ignore


def add_middlewares(app: FastAPI):
    """
    FILO
    """
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TraceMiddleware)


def main():
    settings = get_setting("settings.toml")
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
    root_router.add_api_route("/health", lambda: "health", tags=["health check"])

    app.include_router(root_router, prefix=settings.api.API_VERSION_STR)
    add_exception_handlers(app)
    add_middlewares(app)

    logger.success("server is running now")
    return app


if __name__ == "__main__":
    settings = get_setting()
    modulename = settings.get_modulename(__file__)
    uvicorn.run(  # type: ignore
        f"{modulename}:main",
        host=settings.api.HOST,
        port=settings.api.PORT,
        factory=True,
        reload=True,
        reload_excludes=["test_*.py", "conftest.py"],
        log_config=None,
    )
