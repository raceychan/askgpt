import pytest

from src.app.gpt.service import GPTSystem, SessionActor, UserActor
from src.app.gpt.user import (
    CreateSession,
    CreateUser,
    SendChatMessage,
    SessionCreated,
    UserCreated,
)
from src.domain.config import TestDefaults


@pytest.fixture(scope="module")
def create_user():
    return CreateUser(user_id=TestDefaults.user_id)


@pytest.fixture(scope="module")
def create_session():
    return CreateSession(
        user_id=TestDefaults.user_id, session_id=TestDefaults.session_id
    )


@pytest.fixture(scope="module")
def send_chat_message():
    return SendChatMessage(
        user_id=TestDefaults.user_id,
        session_id=TestDefaults.session_id,
        user_message="hello",
    )


@pytest.fixture(scope="module")
def user_created():
    return UserCreated(user_id=TestDefaults.user_id)


@pytest.fixture(scope="module")
def session_created():
    return SessionCreated(
        user_id=TestDefaults.user_id, session_id=TestDefaults.session_id
    )


@pytest.fixture(scope="module")
def system(settings):
    system = GPTSystem.setup(settings)
    return system


async def test_create_user_by_command(system: GPTSystem, create_user: CreateUser):
    await system.handle(create_user)

    user = system.get_actor(create_user.entity_id)
    assert isinstance(user, UserActor)


async def test_create_session_by_command(
    system: GPTSystem, create_session: CreateSession
):
    user = system.get_actor(create_session.user_id)
    assert isinstance(user, UserActor)

    await user.handle(create_session)
    session = user.get_actor(create_session.entity_id)
    assert isinstance(session, SessionActor)


async def test_create_user_by_event(user_created: UserCreated):
    user = UserActor.apply(user_created)
    assert isinstance(user, UserActor)
    assert user.entity_id == user_created.entity_id


async def test_create_session_by_event(session_created: SessionCreated):
    session = SessionActor.apply(session_created)
    assert isinstance(session, SessionActor)
    assert session.entity_id == session_created.entity_id
