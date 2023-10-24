import asyncio

import pytest
from src.domain.config import Settings
from src.domain.fileutil import FileLoader, FileUtil


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

class TestSettings(Settings):
    __test__ = False

    class DB(Settings.DB):
        DB_DRIVER: str = "sqlite"
        DATABASE: str = ":memory:"
        ENGINE_ECHO: bool = False


@pytest.fixture(scope="module")
def settings() -> TestSettings:
    return TestSettings(OPENAI_API_KEY="fake_api_key", db=TestSettings.DB())


@pytest.fixture(scope="module")
def async_engine(settings: TestSettings):
    from sqlalchemy.ext import asyncio as sa_aio

    engine = sa_aio.create_async_engine(
        settings.db.ASYNC_DB_URL, echo=settings.db.ENGINE_ECHO, pool_pre_ping=True
    )
    return engine


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)
