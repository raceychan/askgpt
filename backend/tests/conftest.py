import asyncio
import pathlib

import pytest
from src.app.auth.model import UserCredential, UserRoles
from src.domain.config import Settings
from src.helpers.file import FileLoader, FileUtil
from src.infra import security


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestDefaults:
    SYSTEM_ID: str = "system"
    USER_ID: str = "5aba4f79-19f7-4bd2-92fe-f2cdb43635a3"
    USER_NAME: str = "admin"
    USER_EMAIL: str = "admin@gmail.com"
    USER_PASSWORD: str = "password"
    SESSION_ID: str = "e0b5ee4a-ef76-4ed9-89fb-5f7a64122dc8"
    SESSION_NAME: str = "default_session"
    MODEL: str = "gpt-3.5-turbo"
    USER_ROLE: UserRoles = UserRoles.user
    USER_INFO: UserCredential = UserCredential(
        user_email=USER_EMAIL,
        user_name=USER_NAME,
        hash_password=security.hash_password(USER_PASSWORD.encode()),
    )


# class TestSettings(Settings):
#     __test__ = False

#     class DB(Settings.DB):
#         DATABASE: pathlib.Path
#         ENGINE_ECHO: bool = False
#         HOST: str | None = None
#         PORT: int | None = -1
#         USER: str | None = None
#         PASSWORD: str | None = None

#     class ActorRefs(Settings.ActorRefs): ...

#     db: DB


@pytest.fixture(scope="session")
def settings() -> Settings:
    ss = Settings(
        RUNTIME_ENV="test",
        actor_refs=Settings.ActorRefs(
            EVENTLOG="test_eventlog", JOURNAL="test_journal", SYSTEM="test_system"
        ),
        db=Settings.SqliteDB(
            DATABASE=":memory:",
            ISOLATION_LEVEL="SERIALIZABLE",
            ENGINE_ECHO=False,
        ),
        redis=Settings.Redis(
            HOST="", PORT=-1, DB="", keyspaces=Settings.Redis.KeySpaces(APP="test")
        ),
        security=Settings.Security(
            SECRET_KEY="test_security", ALGORITHM="HSA", CORS_ORIGINS=["localhost:5732"]
        ),
        api=Settings.API(HOST="localhost", PORT=5000),
        throttling=Settings.Throttling(
            USER_MAX_REQUEST_PER_MINUTE=1, USER_MAX_REQUEST_DURATION_MINUTE=1
        ),
        event_record=Settings.EventRecord(),
        openai_client=Settings.OpenAIClient(),
    )

    return ss


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader: FileLoader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)


@pytest.fixture(scope="session")
def test_defaults():
    return TestDefaults


@pytest.fixture(scope="module")
def token_encrypt(settings: Settings) -> security.Encrypt:
    return security.Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )
