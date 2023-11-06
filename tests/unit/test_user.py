import pytest

from src.app.gpt import model

# from src.infra.mq import MailBox


@pytest.fixture(scope="module")
def create_user():
    return model.CreateUser(user_id=model.TestDefaults.USER_ID)


@pytest.fixture(scope="module")
def create_session():
    return model.CreateSession(
        session_id=model.TestDefaults.SESSION_ID, user_id=model.TestDefaults.USER_ID
    )


@pytest.fixture(scope="module")
def session_created():
    return model.SessionCreated(
        session_id=model.TestDefaults.SESSION_ID, user_id=model.TestDefaults.USER_ID
    )


def test_create_user_via_command(create_user: model.CreateUser):
    user = model.User.create(create_user)
    assert isinstance(user, model.User)
    assert user.entity_id == create_user.entity_id


def test_user_create_session_via_command(
    create_user: model.CreateUser, create_session: model.CreateSession
):
    user = model.User.create(create_user)
    assert user.entity_id == create_session.user_id
    user.create_session(session_id=create_session.entity_id)
    session = user.get_session(session_id=create_session.entity_id)
    assert isinstance(session, model.ChatSession)
    assert session.entity_id == create_session.entity_id


def test_rebuild_user_by_events(
    user_created: model.UserCreated, session_created: model.SessionCreated
):
    user: model.User = model.User.apply(user_created)
    user.apply(session_created)

    assert isinstance(user, model.User)
    assert user.entity_id == user_created.entity_id
    session = user.get_session(session_created.entity_id)
    assert isinstance(session, model.ChatSession)
