import json
import typing as ty

import sqlalchemy as sa
from src.adapters.database import AsyncDatabase
from src.domain.interface import IEvent, IEventStore
from src.domain.model.base import Event

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

table_event_mapping = {
    "id": "event_id",
    "entity_id": "entity_id",
    "event_type": "event_type",
    "gmt_created": "timestamp",
}


def dump_event(event: IEvent) -> dict[str, ty.Any]:
    data = event.asdict(by_alias=False)

    row = {colname: data.pop(field) for colname, field in table_event_mapping.items()}
    row["event_body"] = json.dumps(data)
    row["version"] = event.__class__.version
    return row


def load_event(row_mapping: sa.RowMapping | dict[str, ty.Any]) -> IEvent:
    row = dict(row_mapping)

    data = {field: row.pop(colname) for colname, field in table_event_mapping.items()}
    version, extra = row.pop("version"), row.pop("event_body")
    matched_type = Event.match_event_type(
        event_type=data["event_type"], version=version
    )
    data = data | (extra if isinstance(extra, dict) else json.loads(extra))
    event = matched_type.model_validate(data)
    return event


class EventStore(IEventStore):
    table: sa.TableClause = EVENT_TABLE

    def __init__(self, aiodb: AsyncDatabase):
        self._aiodb = aiodb

    async def add(self, event: IEvent) -> None:
        value = dump_event(event)
        stmt = sa.insert(self.table).values(value)

        async with self._aiodb.begin() as conn:
            await conn.execute(stmt)

    async def add_all(self, events: list[IEvent]) -> None:
        values = [dump_event(event) for event in events]
        sa.insert(self.table).values(values)

    async def get(self, entity_id: str) -> list[IEvent]:
        stmt = sa.select(self.table).where(self.table.c.entity_id == entity_id)
        async with self._aiodb.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]  # type: ignore
        return events

    async def list_all(self) -> list[IEvent]:
        stmt = sa.select(self.table)
        async with self._aiodb.begin() as cursor:
            result = await cursor.execute(stmt)
            rows = result.fetchall()
            events = [load_event(row._mapping) for row in rows]  # type: ignore
        return events

    async def remove(self, entity_id: str) -> None:
        raise NotImplementedError
