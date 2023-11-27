# import uvicorn
# from fastapi import APIRouter, FastAPI

# from src.domain._log import logger
# from src.domain.config import Settings

# settings = Settings.from_file("settings.toml")


# gpt = APIRouter(prefix="/gpt")


# @gpt.get("{question}")
# async def ask(question: str):
#     return "hello"


# def startup(app: FastAPI):
#     async def on_startup() -> None:
#         ...

#     return on_startup


# def shutdown(app: FastAPI):
#     async def on_shutdown() -> None:
#         ...

#     return on_shutdown


# def add_exception_handlers(app: FastAPI):
#     ...
#     # for code, exe_handler in {}.items():
#     #     app.add_exception_handler(code, exe_handler)


# def add_middlewares(app: FastAPI):
#     ...


# def main():
#     app = FastAPI(
#         title=settings.PROJECT_NAME,
#         description="gpt service at your home",
#         version=settings.api.API_VERSION,
#         openapi_url=settings.api.OPEN_API,
#     )

#     root_router = APIRouter()
#     root_router.include_router(gpt, tags=["gpt client service"])
#     root_router.add_api_route("/health", lambda: "health", tags=["health check"])

#     add_exception_handlers(app)
#     add_middlewares(app)

#     app.add_event_handler("startup", startup(app))
#     app.add_event_handler("shutdown", shutdown(app))

#     app.include_router(root_router, prefix=settings.api.API_VERSION_STR)

#     logger.success("proxy server is running now")
#     return app


# if __name__ == "__main__":
#     modulename = settings.get_modulename(__file__)
#     uvicorn.run(f"{modulename}:main", host="127.0.0.1", port=5000, log_level="info")
