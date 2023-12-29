from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import APIRouter, FastAPI
from src.app.api.error_handlers import HandlerRegistry
from src.app.api.middleware import LoggingMiddleware, TraceMiddleware
from src.app.api.router import api_router
from src.app.bootstrap import bootstrap
from src.app.factory import get_eventrecord
from src.domain._log import logger
from src.domain.config import get_setting

stack = AsyncExitStack()

# TODO: implement container to store dependencies
# reff: https://python-dependency-injector.ets-labs.org/examples/fastapi-sqlalchemy.html


class Container:
    """

    a centralized place to store dependencies
    push dependencies to exit stack when initializing them
    pop dependencies from exit stack when exiting them
    for every dependency, instantiate with a factory function

    difference with fastapi.dependencies.Depends:
    1. exit stack
    2. this is for app-wide dependencies, not request-wide dependencies
    3. define a per_request:bool, if true, reinstantiate the dependency for every request

    eg.


    def get_auth_service(
        settings,
        user_repo = Depends(get_user_repo),
        token_registry = Depends(get_token_registry),
        token_encrypt = Depends(get_encryp),
        producer = Depends(get_producer),

    ):
        ...


    auth_service: AuthService = Depends(get_auth_service)
    """

    ...


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_setting()
    await bootstrap(settings)
    record = get_eventrecord(settings)

    async with stack:
        await stack.enter_async_context(record.lifespan())
        yield


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
    # TODO: add throttling middleware


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


def server():
    import uvicorn

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


if __name__ == "__main__":
    server()
