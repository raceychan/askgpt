import pytest

from src.app.gpt import model


@pytest.fixture(scope="module")
def create_user(user_info: model.UserInfo):
    return model.CreateUser(user_id=model.TestDefaults.USER_ID, user_info=user_info)


@pytest.fixture(scope="module")
def create_session():
    return model.CreateSession(
        user_id=model.TestDefaults.USER_ID, session_id=model.TestDefaults.SESSION_ID
    )


@pytest.fixture(scope="module")
def send_chat_message(user_info: model.UserInfo):
    # This should raise Exception
    return model.SendChatMessage(
        user_id=model.TestDefaults.USER_ID,
        session_id=model.TestDefaults.SESSION_ID,
        message_body="hello",
        role="user",
    )


@pytest.fixture(scope="module")
def user_created(user_info: model.UserInfo):
    return model.UserCreated(user_id=model.TestDefaults.USER_ID, user_info=user_info)


@pytest.fixture(scope="module")
def session_created():
    return model.SessionCreated(
        user_id=model.TestDefaults.USER_ID, session_id=model.TestDefaults.SESSION_ID
    )


def test_command_immutable(
    create_user: model.CreateUser, create_session: model.CreateSession
):
    from pydantic import ValidationError

    assert create_user.entity_id == model.TestDefaults.USER_ID
    assert create_session.entity_id == model.TestDefaults.SESSION_ID

    with pytest.raises(ValidationError):
        create_user.entity_id = "new_id"


def test_event_immutable(
    user_created: model.UserCreated, session_created: model.SessionCreated
):
    from pydantic import ValidationError

    assert user_created.entity_id == model.TestDefaults.USER_ID
    assert session_created.session_id == model.TestDefaults.SESSION_ID

    with pytest.raises(ValidationError):
        user_created.entity_id = "new_id"


def test_command_serialize(create_session: model.CreateSession):
    data = create_session.asdict()

    assert data["user_id"] == model.TestDefaults.USER_ID
    assert data["session_id"] == model.TestDefaults.SESSION_ID


def test_event_serialize(
    user_created: model.UserCreated, session_created: model.SessionCreated
):
    data = user_created.asdict()
    assert data["user_id"] == model.TestDefaults.USER_ID
    assert data["event_type"] == "user_created"

    data = session_created.asdict()
    assert data["user_id"] == model.TestDefaults.USER_ID
    assert data["session_id"] == model.TestDefaults.SESSION_ID
    assert data["event_type"] == "session_created"
