import typing as ty

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.sql import type_api as sa_ty

from src.domain.model import Event
from src.domain.service.interface import IEventStore


def as_sa_types(py_type: type) -> sa_ty.TypeEngine:
    import datetime
    import decimal
    import uuid

    TYPES_MAPPING = {
        str: sa.String,
        int: sa.Integer,
        datetime.datetime: sa.DateTime,
        bool: sa.Boolean,
        float: sa.Float,
        list: sa.JSON,
        dict: sa.JSON,
        uuid.UUID: sa.UUID,
        None: sa.Null,
        decimal.Decimal: sa.Numeric,
    }

    return TYPES_MAPPING[py_type]


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


def dump_event(event: Event) -> dict:
    data = event.asdict(by_alias=False)
    return dict(
        id=data.pop("event_id"),
        event_type=data.pop("event_type"),
        entity_id=data.pop("entity_id"),
        version=event.__class__.version,
        event_body=data,
        gmt_created=data.pop("timestamp"),
    )


def load_event(row_mapping: ty.Mapping) -> Event:
    data = dict(row_mapping)
    matched_type = Event.match_event_type(data["event_type"])
    return matched_type(id=data.pop("id"), timestamp=data.pop("gmt_created"), **data)


class EventStore(IEventStore):
    table: sa.TableClause = EVENT_TABLE

    def __init__(self, engine: sa_aio.AsyncEngine):
        self.engine = engine

    async def add(self, event: Event):
        value = dump_event(event)
        stmt = sa.insert(self.table).values(value)
        async with self.engine.begin() as cursor:
            await cursor.execute(stmt)

    async def add_all(self, events: list[Event]):
        values = [dump_event(event) for event in events]
        sa.insert(self.table).values(values)

    async def get(self, entity_id: str) -> list[Event]:
        stmt = sa.select(self.table).where(self.table.c.entity_id == entity_id)
        async with self.engine.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]
        return events

    async def list_all(self):
        stmt = sa.select(self.table)
        async with self.engine.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]
        return events

    async def remove(self, entity_id: str):
        raise NotImplementedError
