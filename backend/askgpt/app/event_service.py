from contextlib import asynccontextmanager

from askgpt.domain.interface import IEvent
from askgpt.infra.eventstore import EventStore


class EventService:
    def __init__(self, event_store: EventStore):
        self._event_store = event_store
        self._event_handlers = {}

    @asynccontextmanager
    async def trans(self):
        async with self._event_store.uow.trans() as uow:
            yield uow

    async def publish(self, events: list[IEvent]):
        """
        async with event_service.trans():
            await user_repo.add(User(name="test"))
            await event_service.publish(UserCreated(entity_id="test", name="test"))
        """
        await self._event_store.add_all(events)
