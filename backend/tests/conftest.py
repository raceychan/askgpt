import asyncio
import pathlib

import pytest
from src.domain.config import Settings
from src.domain.model.test_default import TestDefaults
from src.infra import security
from src.helpers.file import FileLoader, FileUtil


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
        HOST: str | None = None
        PORT: int | None = -1
        USER: str | None = None
        PASSWORD: str | None = None

    class ActorRefs(Settings.ActorRefs):
        ...

    db: DB


@pytest.fixture(scope="session")
def settings() -> TestSettings:
    ss = TestSettings.from_file("test_settings.toml")
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
