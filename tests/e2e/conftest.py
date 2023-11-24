import asyncio
import pathlib

import pytest

from src.domain.config import Settings
from src.domain.fileutil import fileutil


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestSettings(Settings):
    __test__ = False

    class DB(Settings.DB):
        DATABASE: pathlib.Path
        ENGINE_ECHO: bool = False

    class ActorRefs(Settings.ActorRefs):
        ...


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    db_path = pathlib.Path("./database/test.db")
    # db_path = pathlib.Path(":memory:")
    # api_key = fileutil.read_file("settings.toml")["OPENAI_API_KEY"]
    api_key = "fake_api_key"

    db = TestSettings.DB(DATABASE=db_path)
    ss = TestSettings(
        OPENAI_API_KEY=api_key,
        db=db,
        actor_refs=TestSettings.ActorRefs(),
        RUNTIME_ENV="test",
    )
    return ss
