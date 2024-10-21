import pytest

from askgpt.adapters.cache import Cache
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt._repository import SessionRepository
from askgpt.app.gpt.service import OpenAIGPT
from askgpt.app.user.service import UserService
from askgpt.infra.eventstore import EventStore
from askgpt.infra.security import Encryptor
from tests.conftest import UserDefaults


@pytest.fixture(scope="module")
async def gpt_service(
    session_repo: SessionRepository,
    encryptor: Encryptor,
    cache: Cache[str, str],
    user_service: UserService,
    auth_service: AuthService,
    event_store: EventStore,
):

    service = OpenAIGPT(
        encryptor=encryptor,
        user_service=user_service,
        auth_service=auth_service,
        event_store=event_store,
        cache=cache,
        session_repo=session_repo,
    )
    return service


async def test_list_created_session(
    test_defaults: UserDefaults,
    auth_service: AuthService,
    gpt_service: OpenAIGPT,
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

    session = await gpt_service.create_session(user_id)
    user_session = await gpt_service.get_session(user_id, session_id=session.entity_id)
    assert session.entity_id == user_session.entity_id
    assert session.user_id == user_session.user_id == user_id
    assert len(session.messages) == len(user_session.messages)

    sessions = await gpt_service.list_sessions(user_id)

    assert len(sessions) == 1

    _ = await gpt_service.create_session(user_id)
    sessions = await gpt_service.list_sessions(user_id)
    assert len(sessions) == 2


async def test_gpt_send_message_without_api_key():
    """
    raise APINotProvidedError when user tries to send messages
    without providing API-key
    """
