import asyncio
import pathlib

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
        DATABASE: pathlib.Path | str = ":memory:"
        ENGINE_ECHO: bool = True


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    ss = TestSettings(OPENAI_API_KEY="fake_api_key", db=TestSettings.DB())
    return ss


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)
