import asyncio

import pytest

from askgpt.domain.config import SETTINGS_CONTEXT, SecretStr, Settings
from askgpt.helpers.file import FileLoader, FileUtil
from askgpt.helpers.security import generate_secrete
from askgpt.infra import security

from ._const import UserDefaults, dft


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Settings:
    ss = Settings(
        RUNTIME_ENV="test",
        actor_refs=Settings.ActorRefs(
            EVENTLOG="test_eventlog",
            SYSTEM="test_system",
        ),
        db=Settings.SqliteDB(
            DATABASE=":memory:",
            ISOLATION_LEVEL="SERIALIZABLE",
            # ENGINE_ECHO=False,
        ),
        redis=Settings.Redis(
            HOST="localhost",
            PORT=0,
            DB="",
            keyspaces=Settings.Redis.KeySpaces(APP="test"),  # type: ignore
        ),
        security=Settings.Security(
            SECRET_KEY=SecretStr(generate_secrete().decode()),
            ALGORITHM="HS256",
            CORS_ORIGINS=["localhost:5732"],
            ACCESS_TOKEN_EXPIRE_MINUTES=15,
        ),
        api=Settings.API(HOST="localhost", PORT=5000),
        throttling=Settings.Throttling(
            USER_MAX_REQUEST_PER_MINUTE=1, USER_MAX_REQUEST_DURATION_MINUTE=1
        ),
        event_record=Settings.EventRecord(),
        openai_client=Settings.OpenAIClient(),
    )
    SETTINGS_CONTEXT.set(ss)
    return ss


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader: FileLoader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)


@pytest.fixture(scope="session")
def test_defaults() -> UserDefaults:
    return dft


@pytest.fixture(scope="module")
def encryptor(settings: Settings) -> security.Encryptor:
    return security.Encryptor(
        secret_key=settings.security.SECRET_KEY.get_secret_value(),
        algorithm=settings.security.ALGORITHM,
    )
