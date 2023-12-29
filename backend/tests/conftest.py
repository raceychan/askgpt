import asyncio
import pathlib

import pytest
from src.domain.config import Settings
from src.domain.model.test_default import TestDefaults
from src.infra import encrypt
from src.infra.fileutil import FileLoader, FileUtil


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
def token_encrypt(settings: Settings) -> encrypt.Encrypt:
    return encrypt.Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )
