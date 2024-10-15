import pytest
from askgpt.adapters.uow import UnitOfWork
from askgpt.app.gpt.repository import SessionRepository


@pytest.fixture(scope="module")
async def session_repo(uow: UnitOfWork):
    return SessionRepository(uow)
