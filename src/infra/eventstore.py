import typing as ty

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

from src.app.actor import Actor
from src.domain.model import Envelope, Event, Message


def table_parser(event: Event):
    return dict(
        id=event.event_id,
        event_type=event.event_type,
        entity_id=event.entity_id,
        version=event.version,
    )


class EventStore(Actor):
    def __init__(self, engine: sa_aio.AsyncEngine, event_table: sa.TableClause):
        self.engine = engine
        self.event_table = event_table

    async def handle(self, message: Message):
        if not isinstance(message, Event):
            raise TypeError(f"Unexpected message type: {type(message)}")

        await self.add(message)

    async def add(self, event: Event):
        value = table_parser(event)
        stmt = sa.insert(self.event_table).values(value)

        async with self.engine.begin() as cursor:
            await cursor.execute(stmt)

    async def add_all(self, events: list[Event]):
        values = [Envelope(payload=event).model_dump() for event in events]
        sa.insert(self.event_table).values(values)

    async def get(self, entity_id: str) -> list[Event]:
        stmt = sa.select(self.event_table).where(
            self.event_table.c.entity_id == entity_id
        )
        async with self.engine.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            envets = [Event.model_validate(row, from_attributes=True) for row in rows]
        return envets

    async def remove(self, entity_id: str):
        ...
