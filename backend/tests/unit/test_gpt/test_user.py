import pytest

from askgpt.app.gpt._model import (
    CreateSession,
    CreateUser,
    SessionCreated,
    User,
    UserCreated,
)
from tests.conftest import dft


@pytest.fixture(scope="module")
def create_user():
    return CreateUser(user_id=dft.USER_ID)


@pytest.fixture(scope="module")
def create_session():
    return CreateSession(session_id=dft.SESSION_ID, user_id=dft.USER_ID)


@pytest.fixture(scope="module")
def session_created():
    return SessionCreated(
        session_id=dft.SESSION_ID,
        user_id=dft.USER_ID,
        session_name="New Session",
    )


def test_create_user_via_command(create_user: CreateUser):
    # TODO: we should not create user actor
    user = User.create(create_user)
    assert isinstance(user, User)
    assert user.entity_id == create_user.entity_id


def test_rebuild_user_by_events(
    user_created: UserCreated, session_created: SessionCreated
):
    user: User = User.apply(user_created)
    user.apply(session_created)

    assert isinstance(user, User)
    assert user.entity_id == user_created.entity_id
    assert session_created.session_id in user.session_ids


# def test_user_password(user_info: UserInfo):
#     assert encrypt.verify_password(
#         dft.USER_PASSWORD.encode(), user_info.hash_password
#     )
