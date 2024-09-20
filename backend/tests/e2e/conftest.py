import asyncio
import pathlib

import pytest
from askgpt.domain.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestSettings(Settings):
    __test__ = False

    class DB(Settings.DB):
        DIALECT: str = "sqlite"
        DRIVER: str = "aiosqlite"
        DATABASE: pathlib.Path = pathlib.Path("./database/test.db")
        ENGINE_ECHO: bool = False
        HOST: str | None = None
        PORT: int | None = None
        USER: str | None = None
        PASSWORD: str | None = None

    class ActorRefs(Settings.ActorRefs): ...

    db: DB = DB(ISOLATION_LEVEL="SERIALIZABLE")


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    ss = TestSettings(
        actor_refs=TestSettings.ActorRefs(),
        RUNTIME_ENV="test",
        api=TestSettings.API(HOST="localhost", PORT=8000, API_VERSION="0.1.0"),
        security=TestSettings.Security(SECRET_KEY="test", ALGORITHM="HS256"),
        redis=TestSettings.Redis(
            HOST="localhost",
            PORT=6379,
            DB=1,
            SOCKET_TIMEOUT=2,
            keyspaces=TestSettings.Redis.KeySpaces(APP="test"),
        ),
        event_record=TestSettings.EventRecord(),
    )
    return ss
