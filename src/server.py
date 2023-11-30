from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI

from src.app.bootstrap import bootstrap
from src.app.factory import get_async_engine
from src.app.gpt.api import gpt_router
from src.domain._log import logger
from src.domain.config import get_setting


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_async_engine(get_setting())
    await bootstrap(engine)
    yield


def add_exception_handlers(app: FastAPI):
    return
    app.add_exception_handler()


def add_middlewares(app: FastAPI):
    return
    app.add_middleware()


def main():
    settings = get_setting("settings.toml")
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="gpt service at your home",
        version=settings.api.API_VERSION,
        openapi_url=settings.api.OPEN_API,
        lifespan=lifespan,
    )

    root_router = APIRouter()
    root_router.include_router(gpt_router, tags=["gpt client service"])
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
        f"{modulename}:main", host="127.0.0.1", port=5000, log_level="info", reload=True
    )
