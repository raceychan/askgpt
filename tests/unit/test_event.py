import pytest

from src.app.service.gpt import UserCreated
from src.domain.model import Event


@pytest.fixture
def entity_id():
    return "test_id"


@pytest.fixture
def event(entity_id):
    return Event(entity_id=entity_id)


@pytest.fixture
def user_created(entity_id):
    return UserCreated(user_id=entity_id)


def test_rebuild_event(user_created: UserCreated):
    data = user_created.model_dump()
    e = Event.rebuild(data)
    assert isinstance(e, UserCreated)
    assert hash(user_created) == hash(e)


# @pytest.fixture
# def envelope(event):
#    enve = Envelope(event)
