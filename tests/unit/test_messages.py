import pytest

from src.app.gpt.model import (
    CreateSession,
    CreateUser,
    SendChatMessage,
    SessionCreated,
    TestDefaults,
    UserCreated,
)


@pytest.fixture(scope="module")
def create_user():
    return CreateUser(user_id=TestDefaults.USER_ID)


@pytest.fixture(scope="module")
def create_session():
    return CreateSession(
        user_id=TestDefaults.USER_ID, session_id=TestDefaults.SESSION_ID
    )


@pytest.fixture(scope="module")
def send_chat_message():
    return SendChatMessage(
        user_id=TestDefaults.USER_ID,
        session_id=TestDefaults.SESSION_ID,
        user_message="hello",
    )


@pytest.fixture(scope="module")
def user_created():
    return UserCreated(user_id=TestDefaults.USER_ID)


@pytest.fixture(scope="module")
def session_created():
    return SessionCreated(
        user_id=TestDefaults.USER_ID, session_id=TestDefaults.SESSION_ID
    )


def test_command_immutable(create_user, create_session):
    from pydantic import ValidationError

    assert create_user.entity_id == TestDefaults.USER_ID
    assert create_session.entity_id == TestDefaults.SESSION_ID

    with pytest.raises(ValidationError):
        create_user.entity_id = "new_id"


def test_event_immutable(user_created, session_created):
    from pydantic import ValidationError

    assert user_created.entity_id == TestDefaults.USER_ID
    assert session_created.entity_id == TestDefaults.SESSION_ID

    with pytest.raises(ValidationError):
        user_created.entity_id = "new_id"


def test_command_serialize(create_session):
    data = create_session.asdict()

    assert data["user_id"] == TestDefaults.USER_ID
    assert data["session_id"] == TestDefaults.SESSION_ID


def test_event_serialize(user_created, session_created):
    data = user_created.asdict()
    assert data["user_id"] == TestDefaults.USER_ID
    assert data["event_type"] == "user_created"

    data = session_created.asdict()
    assert data["user_id"] == TestDefaults.USER_ID
    assert data["session_id"] == TestDefaults.SESSION_ID
    assert data["event_type"] == "session_created"
