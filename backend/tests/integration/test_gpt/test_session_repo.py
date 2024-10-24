from askgpt.app.gpt._model import ChatSession
from askgpt.app.gpt._repository import SessionRepository
from askgpt.helpers.sql import UnitOfWork
from tests.conftest import UserDefaults


async def test_create_and_list_sessions(
    session_repo: SessionRepository,
    test_defaults: UserDefaults,
    uow: UnitOfWork,
):
    ss = ChatSession(
        user_id=test_defaults.USER_ID,
        session_id=test_defaults.SESSION_ID,
        session_name=test_defaults.SESSION_NAME,
    )
    async with uow.trans():
        await session_repo.add(ss)
        sessions = await session_repo.list_sessions(user_id=test_defaults.USER_ID)

    assert sessions
    assert sessions[0].session_name == test_defaults.SESSION_NAME
    assert sessions[0].entity_id == test_defaults.SESSION_ID
