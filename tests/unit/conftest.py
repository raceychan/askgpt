import pytest

from src.domain.fileutil import FileLoader, FileUtil


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)
