import pytest

from src.app.gpt.user import UserCreated
from src.domain.config import Settings
from src.infra.eventstore import EventStore, dump_event, load_event


def test_settins(settings):
    assert isinstance(settings, Settings)

@pytest.fixture(scope="module")
def user_created():
    event = UserCreated(user_id="race")
    return event


def test_dump_event_does_not_lose_timestamp(user_created):
    data = dump_event(user_created)
    assert data["gmt_created"] == user_created.timestamp
    assert load_event(data).timestamp == user_created.timestamp


async def test_insert_event(eventstore: EventStore, user_created):
    await eventstore.add(user_created)
    events = await eventstore.get(user_created.entity_id)
    e = events[0]
    assert e.event_id == user_created.event_id
    assert hash(e) == hash(user_created)


async def test_list_event(eventstore: EventStore, user_created):
    es = await eventstore.list_all()
    e = es[0]
    assert e.event_type == "user_created"
    assert e.event_id == user_created.event_id
    assert hash(e) == hash(user_created)
