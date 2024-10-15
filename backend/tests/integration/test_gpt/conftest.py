import pytest

from askgpt.adapters.cache import MemoryCache
from askgpt.adapters.queue import MessageProducer
from askgpt.domain import config
from askgpt.app.actor import QueueBox
from askgpt.app.gpt.repository import SessionRepository
from askgpt.app.gpt.service import GPTSystem
from askgpt.infra.eventstore import EventStore
from askgpt.infra.uow import UnitOfWork


@pytest.fixture(scope="module")
async def gpt_system(
    settings: config.Settings,
    eventstore: EventStore,
    producer: MessageProducer,
    cache: MemoryCache,
):
    system = GPTSystem(
        boxfactory=QueueBox,
        ref=settings.actor_refs.SYSTEM,
        settings=settings,
        producer=producer,
        event_store=eventstore,
        cache=cache,
    )
    await system.start()
    return system


@pytest.fixture(scope="module")
async def session_repo(uow: UnitOfWork):
    return SessionRepository(uow)
