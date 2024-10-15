import typing as ty

import sqlalchemy as sa
from askgpt.adapters.queue import MessageProducer
from askgpt.adapters.uow import UnitOfWork
from askgpt.domain.config import UTC_TZ
from askgpt.domain.interface import IEvent, IEventStore
from askgpt.domain.model.base import Event, json_dumps, json_loads
from askgpt.infra.schema import EventSchema

table_event_mapping = {
    "id": "event_id",
    "entity_id": "entity_id",
    "event_type": "event_type",
    "gmt_created": "timestamp",
}


def dump_event(event: IEvent) -> dict[str, ty.Any]:
    data = event.asdict(by_alias=False)

    row = {colname: data.pop(field) for colname, field in table_event_mapping.items()}
    row["event_body"] = json_dumps(data)
    row["version"] = event.__class__.version
    return row


def load_event(row_mapping: sa.RowMapping | dict[str, ty.Any]) -> IEvent:
    row = dict(row_mapping)

    data = {field: row.pop(colname) for colname, field in table_event_mapping.items()}
    version, extra = row.pop("version"), row.pop("event_body")
    matched_type = Event.match_event_type(
        event_type=data["event_type"], version=version
    )
    data = data | (extra if isinstance(extra, dict) else json_loads(extra))
    data["timestamp"] = data["timestamp"].replace(tzinfo=UTC_TZ)
    event = matched_type.model_validate(data)
    return event


class EventStore(IEventStore):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def add(self, event: IEvent) -> None:
        value = dump_event(event)
        stmt = sa.insert(EventSchema).values(value)
        await self._uow.execute(stmt)

    async def add_all(self, events: list[IEvent]) -> None:
        values = [dump_event(event) for event in events]
        stmt = sa.insert(EventSchema).values(values)
        await self._uow.execute(stmt)

    async def get(self, entity_id: str) -> list[IEvent]:
        stmt = sa.select(EventSchema).where(EventSchema.entity_id == entity_id)
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def get_by_type(self, entity_id: str, event_type: str) -> list[IEvent]:
        stmt = (
            sa.select(EventSchema)
            .where(EventSchema.entity_id == entity_id)
            .where(EventSchema.event_type == event_type)
        )
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def list_all(self) -> list[IEvent]:
        stmt = sa.select(EventSchema)
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def remove(self, entity_id: str) -> None:
        raise NotImplementedError


class OutBoxProducer(MessageProducer[IEvent]):
    """
    a dumb implementation of the producer that just adds the event to the event store
    when we have cdc, we need to publish the event from cdc to the message queue
    """

    def __init__(self, eventstore: EventStore):
        self._es = eventstore

    async def publish(self, message: IEvent):
        await self._es.add(message)
