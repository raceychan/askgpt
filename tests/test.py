import asyncio
import sqlalchemy as sa
from rich import print
from dataclasses import dataclass
from pathlib import Path

from domain.config import Config
from domain.model import AskAnswered, Ask, AskHistory, Envelope, uuid_factory

from infra.eventstore import EventStore, EVENT_TABLE, create_table


def test_all():
    test_db()
    test_event()
    test_envelope()
    print("finished all tests")


@dataclass(frozen=True, slots=True, kw_only=True)
class TestConfig(Config):
    DB_URL: str = "sqlite+aiosqlite:///:memory:"


def test_db():
    db_url = "./eventstore.db"
    engine = sa.create_engine(f"sqlite+aiosqlite:///{db_url}:", echo=True)
    # return EventStore(engine)


def test_event():
    ask = Ask(question="what is your name?")
    e = AskAnswered(ask=ask, entity_id=uuid_factory())
    print(e)


def test_envelope():
    history = AskHistory()
    ask = Ask(question="what is your name?")
    e = AskAnswered(ask=ask, entity_id=history.history_id)
    envelope = Envelope(payload=e)
    data = envelope.model_dump()
    print(data)
    assert envelope.event_id == e.event_id


# async def create_table(engine):
#     sql = Path("../database/eventstore.sql")
#     async with engine.begin() as conn:
#         stmt = sa.text(sql.read_text())
#         await conn.execute(stmt)


async def test_eventstore():
    from sqlalchemy.ext import asyncio as sa_aio

    engine = sa_aio.create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=True, pool_pre_ping=True
    )
    await create_table(engine)

    es = EventStore(engine, EVENT_TABLE)

    entity_id = uuid_factory()

    ask = Ask(question="what is your name?")
    e = AskAnswered(ask=ask, entity_id=entity_id)
    # envelope = Envelope(payload=e)

    await es.add(e)


t = test_eventstore()

asyncio.run(t)
