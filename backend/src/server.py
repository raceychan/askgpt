import functools

from src.app.app import app_factory
from src.domain import config


def server() -> None:
    config.sys_finetune()
    settings = config.get_setting("settings.toml")
    factory = functools.partial(app_factory, settings)
    uvicorn.run(  # type: ignore
        factory,
        host=settings.api.HOST,
        port=settings.api.PORT,
        factory=True,
        reload=True,
        reload_excludes=["test_*.py", "conftest.py"],
        log_config=None,
    )


if __name__ == "__main__":
    import uvicorn

    server()
