import pytest

from src.app.gpt.user import UserCreated
from src.domain.model import Event


@pytest.fixture(scope="package")
def entity_id():
    return "test_id"


@pytest.fixture(scope="package")
def event(entity_id):
    return Event(entity_id=entity_id)


@pytest.fixture(scope="package")
def user_created(entity_id):
    return UserCreated(user_id=entity_id)
