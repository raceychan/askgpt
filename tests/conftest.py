import pytest

from src.domain.config import Settings


@pytest.fixture(scope="session")
def settings():
    return Settings.from_file()
