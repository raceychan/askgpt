import pytest
from tests.conftest import UserDefaults

from askgpt.adapters.queue import MessageProducer
from askgpt.app.auth.repository import UserRepository
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt.repository import SessionRepository
from askgpt.app.gpt.service import GPTService, GPTSystem, SystemState
from askgpt.domain.interface import IEvent
from askgpt.infra.security import Encryptor
from askgpt.infra.uow import UnitOfWork


@pytest.fixture(scope="module")
async def gpt_service(
    gpt_system: GPTSystem,
    uow: UnitOfWork,
    session_repo: SessionRepository,
    encryptor: Encryptor,
    producer: MessageProducer[IEvent],
):

    user_repo = UserRepository(uow)
    service = GPTService(
        system=gpt_system,
        encryptor=encryptor,
        user_repo=user_repo,
        session_repo=session_repo,
        producer=producer,
    )
    async with service.lifespan():
        yield service


@pytest.mark.skip(reason="TODO: fix this test")
async def test_start_when_already_running(gpt_service: GPTService):
    gpt_service.state = SystemState.running
    await gpt_service.start()
    assert gpt_service.state.is_running

    # Assert that no further actions are taken if the state is already running
    assert gpt_service.system.state.is_running

    await gpt_service.stop()
    assert gpt_service.state.is_stopped


async def test_list_created_session(
    test_defaults: UserDefaults,
    auth_service: AuthService,
    gpt_service: GPTService,
    uow: UnitOfWork,
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
    user = await auth_service.find_user(test_defaults.USER_EMAIL)
    assert user
    user_id = user.entity_id

    session = await gpt_service.create_session(user_id)

    actor = await gpt_service.get_session_actor(user_id, session_id=session.entity_id)
    user_session = actor.entity
    assert session.entity_id == user_session.entity_id
    assert session.user_id == user_session.user_id == user_id
    assert len(session.messages) == len(user_session.messages)

    sessions = await gpt_service.list_sessions(user_id)

    assert len(sessions) == 1

    second_ss = await gpt_service.create_session(user_id)
    sessions = await gpt_service.list_sessions(user_id)
    assert len(sessions) == 2


async def test_gpt_send_message_without_api_key():
    """
    raise APINotProvidedError when user tries to send messages
    without providing API-key
    """
