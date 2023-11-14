import asyncio
import pathlib

import pytest

from src.domain.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestSettings(Settings):
    __test__ = False

    class DB(Settings.DB):
        DATABASE: pathlib.Path = pathlib.Path(":memory:")
        # DATABASE: pathlib.Path = pathlib.Path("./database/test.db")
        ENGINE_ECHO: bool = True

    class ActorRefs(Settings.ActorRefs):
        ...


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    db = TestSettings.DB()
    ss = TestSettings(
        OPENAI_API_KEY="fake_api_key",
        db=db,
        actor_refs=TestSettings.ActorRefs(),
        RUNTIME_ENV="test",
    )
    return ss
