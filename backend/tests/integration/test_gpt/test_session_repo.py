from tests.conftest import UserDefaults

from askgpt.app.gpt import model, repository
from askgpt.infra.uow import UnitOfWork


async def test_create_and_list_sessions(
    session_repo: repository.SessionRepository,
    test_defaults: UserDefaults,
    uow: UnitOfWork,
):
    ss = model.ChatSession(
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
