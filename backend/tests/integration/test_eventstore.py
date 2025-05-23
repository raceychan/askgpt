import pytest

from askgpt.app.gpt._model import UserCreated
from askgpt.domain.config import Settings
from askgpt.infra.eventstore import EventStore, dump_event, load_event
from tests.conftest import dft


def test_settins(settings: Settings):
    assert isinstance(settings, Settings)


@pytest.fixture(scope="module")
def user_created():
    event = UserCreated(user_id=dft.USER_ID)
    return event


def test_dump_event_does_not_lose_timestamp(user_created: UserCreated):
    data = dump_event(user_created)
    assert data["gmt_created"] == user_created.timestamp
    assert load_event(data).timestamp == user_created.timestamp


async def test_insert_event(eventstore: EventStore, user_created: UserCreated):
    async with eventstore.uow.trans():
        await eventstore.add(user_created)
        events = await eventstore.get(user_created.entity_id)
        e = events[0]

    assert e.event_id == user_created.event_id
    assert hash(e) == hash(user_created)


async def test_list_event(eventstore: EventStore, user_created: UserCreated):
    async with eventstore.uow.trans():
        es = await eventstore.list_all()
        e = es[0]
        assert e.event_type == "user_created"
        assert e.event_id == user_created.event_id

        assert e.timestamp == user_created.timestamp

        assert hash(e) == hash(user_created)
