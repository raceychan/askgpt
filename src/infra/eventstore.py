import typing as ty

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

from src.domain import Event, IEventStore

EVENT_TABLE: ty.Final[sa.TableClause] = sa.table(
    "domain_events",
    sa.column("id", sa.String),
    sa.column("event_type", sa.String),
    sa.column("event_body", sa.JSON),
    sa.column("entity_id", sa.String),
    sa.column("version", sa.String),
    sa.column("gmt_modified", sa.DateTime),
    sa.column("gmt_created", sa.DateTime),
)


def dump_event(event: Event) -> dict[str, ty.Any]:
    data = event.asdict(by_alias=False)
    return dict(
        id=data.pop("event_id"),
        entity_id=data.pop("entity_id"),
        gmt_created=data.pop("timestamp"),
        event_type=data.pop("event_type"),
        event_body=data,
        version=event.__class__.version,
    )


def load_event(row_mapping: sa.RowMapping | dict[str, ty.Any]) -> Event:
    data = dict(row_mapping)
    matched_type = Event.match_event_type(data["event_type"])
    event_id = data.pop("id")
    entity_id = data.pop("entity_id")
    timestamp = data.pop("gmt_created")
    body = data.pop("event_body")

    return matched_type(id=event_id, entity_id=entity_id, timestamp=timestamp, **body)


class EventStore(IEventStore):
    table: sa.TableClause = EVENT_TABLE

    def __init__(self, engine: sa_aio.AsyncEngine):
        self.engine = engine

    async def add(self, event: Event) -> None:
        value = dump_event(event)
        stmt = sa.insert(self.table).values(value)

        async with self.engine.begin() as cursor:
            await cursor.execute(stmt)

    async def add_all(self, events: list[Event]) -> None:
        values = [dump_event(event) for event in events]
        sa.insert(self.table).values(values)

    async def get(self, entity_id: str) -> list[Event]:
        stmt = sa.select(self.table).where(self.table.c.entity_id == entity_id)
        async with self.engine.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]
        return events

    async def list_all(self) -> list[Event]:
        stmt = sa.select(self.table)
        async with self.engine.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]
        return events

    async def remove(self, entity_id: str) -> None:
        raise NotImplementedError

    @classmethod
    def build(cls, *, db_url: str) -> ty.Self:
        return cls(engine=sa_aio.create_async_engine(db_url))
