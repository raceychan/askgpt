import asyncio
from pathlib import Path

import pytest
import sqlalchemy as sa
from rich import print

from src.domain.config import Settings, frozen
from src.infra.eventstore import EventStore


@pytest.fixture(scope="module")
def settings():
    class TestConfig(Settings):
        class DB(Settings.DB):
            DB_DRIVER: str = "sqlite"
            DATABASE: str = ":memory"

    return TestConfig(OPENAI_API_KEY="fake_api_key", db=TestConfig.DB())


def test_settins(settings):
    assert isinstance(settings, Settings)


# def test_envelope():
#     history = AskHistory()
#     ask = Ask(question="what is your name?")
#     e = AskAnswered(ask=ask, entity_id=history.history_id)
#     envelope = Envelope(payload=e)
#     data = envelope.model_dump()
#     print(data)
#     assert envelope.event_id == e.event_id


# async def create_table(engine):
#     sql = Path("../database/eventstore.sql")
#     async with engine.begin() as conn:
#         stmt = sa.text(sql.read_text())
#         await conn.execute(stmt)


# async def test_eventstore():
#     from sqlalchemy.ext import asyncio as sa_aio

#     engine = sa_aio.create_async_engine(
#         "sqlite+aiosqlite:///:memory:", echo=True, pool_pre_ping=True
#     )
#     await create_table(engine)

#     es = EventStore(engine, EVENT_TABLE)

#     entity_id = uuid_factory()

#     ask = Ask(question="what is your name?")
#     e = AskAnswered(ask=ask, entity_id=entity_id)
#     # envelope = Envelope(payload=e)

#     await es.add(e)


# t = test_eventstore()

# asyncio.run(t)
