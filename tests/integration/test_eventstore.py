import pytest

from src.app.gpt.user import UserCreated
from src.domain.config import Settings
from src.infra.eventstore import EventStore, dump_event, load_event
from src.infra.schema import EventSchema


@pytest.fixture(autouse=True)
async def event_table(async_engine):
    await EventSchema.create_table_async(async_engine)


@pytest.fixture()
async def event_store(async_engine) -> EventStore:
    es = EventStore(async_engine)
    return es


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


async def test_insert_event(event_store: EventStore, user_created):
    await event_store.add(user_created)
    events = await event_store.get(user_created.entity_id)
    e = events[0]
    assert e.event_id == user_created.event_id
    assert hash(e) == hash(user_created)


async def test_list_event(event_store: EventStore, user_created):
    es = await event_store.list_all()
    e = es[0]
    assert e.event_type == "user_created"
    assert e.event_id == user_created.event_id
    assert hash(e) == hash(user_created)
