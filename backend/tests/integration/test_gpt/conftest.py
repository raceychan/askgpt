import pytest

from askgpt.helpers.sql import UnitOfWork
from askgpt.app.gpt._repository import SessionRepository
from askgpt.app.gpt.service import SessionService
from askgpt.infra.eventstore import EventStore


@pytest.fixture(scope="module")
async def session_repo(uow: UnitOfWork):
    return SessionRepository(uow)


@pytest.fixture(scope="module")
async def session_service(session_repo: SessionRepository, event_store: EventStore):
    return SessionService(session_repo, event_store)
