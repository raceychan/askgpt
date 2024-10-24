import pytest

from askgpt.adapters.cache import Cache
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt.service import OpenAIGPT, SessionService
from askgpt.app.user.service import UserService
from askgpt.infra.eventstore import EventStore
from tests.conftest import UserDefaults


@pytest.fixture(scope="module")
async def openai_service(
    session_service: SessionService,
    cache: Cache[str, str],
    auth_service: AuthService,
    event_store: EventStore,
):
    service = OpenAIGPT(
        auth_service=auth_service,
        event_store=event_store,
        cache=cache,
        session_service=session_service,
    )
    return service


async def test_list_created_session(
    test_defaults: UserDefaults,
    auth_service: AuthService,
    session_service: SessionService,
    user_service: UserService,
):
    """
    TO FIX BUG: when user create a session,
    and then get session via the session_id,
    OrphanSession error would be raised
    # cause: not using transaction, leads to rollback
    """
    await auth_service.signup_user(
        user_name=test_defaults.USER_NAME,
        email=test_defaults.USER_EMAIL,
        password=test_defaults.USER_PASSWORD,
    )
    user = await user_service.find_user(test_defaults.USER_EMAIL)
    assert user
    user_id = user.entity_id

    session = await session_service.create_session(user_id)
    user_session = await session_service.get_session(
        user_id, session_id=session.entity_id
    )
    assert session.entity_id == user_session.entity_id
    assert session.user_id == user_session.user_id == user_id
    assert len(session.messages) == len(user_session.messages)

    sessions = await session_service.list_sessions(user_id)

    assert len(sessions) == 1

    _ = await session_service.create_session(user_id)
    sessions = await session_service.list_sessions(user_id)
    assert len(sessions) == 2


async def test_gpt_send_message_without_api_key():
    """
    raise APINotProvidedError when user tries to send messages
    without providing API-key
    """
