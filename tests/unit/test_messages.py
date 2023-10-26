import pytest
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


def test_command_immutable(create_user, create_session):
    from pydantic import ValidationError

    assert create_user.entity_id == TestDefaults.user_id
    assert create_session.entity_id == TestDefaults.session_id

    with pytest.raises(ValidationError):
        create_user.entity_id = "new_id"


def test_event_immutable(user_created, session_created):
    from pydantic import ValidationError

    assert user_created.entity_id == TestDefaults.user_id
    assert session_created.entity_id == TestDefaults.session_id

    with pytest.raises(ValidationError):
        user_created.entity_id = "new_id"


def test_command_serialize(create_user, create_session):
    data = create_user.asdict()
    data["user_id"] == TestDefaults.user_id

    data = create_session.asdict()
    assert data["user_id"] == TestDefaults.user_id
    assert data["session_id"] == TestDefaults.session_id


def test_event_serialize(user_created, session_created):
    data = user_created.asdict()
    assert data["user_id"] == TestDefaults.user_id
    assert data["event_type"] == "user_created"

    data = session_created.asdict()
    assert data["user_id"] == TestDefaults.user_id
    assert data["session_id"] == TestDefaults.session_id
    assert data["event_type"] == "session_created"
