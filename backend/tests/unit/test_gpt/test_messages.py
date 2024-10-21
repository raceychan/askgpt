import pytest

from askgpt.app.gpt._model import (
    CreateSession,
    CreateUser,
    SendChatMessage,
    SessionCreated,
    UserCreated,
)
from tests.conftest import dft


@pytest.fixture(scope="module")
def create_user():  # user_info: model.UserInfo):
    return CreateUser(user_id=dft.USER_ID)


@pytest.fixture(scope="module")
def create_session():
    return CreateSession(user_id=dft.USER_ID, session_id=dft.SESSION_ID)


@pytest.fixture(scope="module")
def send_chat_message():  # user_info: model.UserInfo):
    # This should raise Exception
    return SendChatMessage(
        user_id=dft.USER_ID,
        session_id=dft.SESSION_ID,
        message_body="hello",
        role="user",
    )


@pytest.fixture(scope="module")
def user_created():  # user_info: model.UserInfo):
    return UserCreated(user_id=dft.USER_ID)


@pytest.fixture(scope="module")
def session_created():
    return SessionCreated(
        user_id=dft.USER_ID,
        session_id=dft.SESSION_ID,
        session_name="New Session",
    )


def test_command_immutable(create_user: CreateUser, create_session: CreateSession):
    from pydantic import ValidationError

    assert create_user.entity_id == dft.USER_ID
    assert create_session.entity_id == dft.SESSION_ID

    with pytest.raises(ValidationError):
        create_user.entity_id = "new_id"


def test_event_immutable(user_created: UserCreated, session_created: SessionCreated):
    from pydantic import ValidationError

    assert user_created.entity_id == dft.USER_ID
    assert session_created.session_id == dft.SESSION_ID

    with pytest.raises(ValidationError):
        user_created.entity_id = "new_id"


def test_command_serialize(create_session: CreateSession):
    data = create_session.asdict()

    assert data["user_id"] == dft.USER_ID
    assert data["session_id"] == dft.SESSION_ID


def test_event_serialize(user_created: UserCreated, session_created: SessionCreated):
    data = user_created.asdict()
    assert data["user_id"] == dft.USER_ID
    assert data["event_type"] == "user_created"

    data = session_created.asdict()
    assert data["user_id"] == dft.USER_ID
    assert data["session_id"] == dft.SESSION_ID
    assert data["event_type"] == "session_created"
