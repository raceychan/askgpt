import typing as ty

import sqlalchemy as sa

# from askgpt.adapters.queue import MessageProducer
from askgpt.domain.interface import IEvent, IEventStore
from askgpt.domain.model.base import Event, json_dumps, json_loads
from askgpt.domain.types import UTC_TZ
from askgpt.infra.schema import DomainEventsTable
from askgpt.helpers.sql import UnitOfWork

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

    @property
    def uow(self) -> UnitOfWork:
        return self._uow

    async def add(self, event: IEvent) -> None:
        value = dump_event(event)
        stmt = sa.insert(DomainEventsTable).values(value)
        await self._uow.execute(stmt)

    async def add_all(self, events: list[IEvent]) -> None:
        values = [dump_event(event) for event in events]
        stmt = sa.insert(DomainEventsTable).values(values)
        await self._uow.execute(stmt)

    async def get(self, entity_id: str) -> list[IEvent]:
        stmt = sa.select(DomainEventsTable).where(
            DomainEventsTable.entity_id == entity_id
        )
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def get_by_type(self, entity_id: str, event_type: str) -> list[IEvent]:
        stmt = sa.select(DomainEventsTable).where(
            DomainEventsTable.entity_id == entity_id,
            DomainEventsTable.event_type == event_type,
        )
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def list_all(self) -> list[IEvent]:
        stmt = sa.select(DomainEventsTable)
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        events = [load_event(row) for row in rows]
        return events

    async def remove(self, entity_id: str) -> None:
        """
        remove all events for the entity
        we probably don't need this, and should avoid remove events in general
        """
        raise NotImplementedError

    # ===========Beta===========

    async def mark_event_consumed(self, *event_ids: str) -> None:
        raise NotImplementedError

    async def list_pending_events(self) -> list[IEvent]:
        """
        select * from EventSchema where consumed_at is null
        """
        raise NotImplementedError

    async def clear_dispatched_events(self) -> None:
        """
        delete from EventSchema where consumed_at is not null
        """
        raise NotImplementedError

    async def transfer_event_to_task(self, event: IEvent) -> None:
        """
        1. update EventSchema set consumed_at = now() where event_id in (event_ids)
        2. insert the events into EventTaskSchedule
        """
        raise NotImplementedError

    async def update_event_task_status(self, event: IEvent) -> None:
        """
        update EventTaskSchedule set status = 'consumed' where event_id = event.id
        """
        raise NotImplementedError
