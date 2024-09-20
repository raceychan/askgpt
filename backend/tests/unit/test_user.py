import pytest
from askgpt.app.gpt import model
from tests.conftest import TestDefaults

# from askgpt.infra import encrypt


@pytest.fixture(scope="module")
def create_user():  # user_info: model.UserInfo):
    return model.CreateUser(user_id=TestDefaults.USER_ID)  # , user_info=user_info)


@pytest.fixture(scope="module")
def create_session():
    return model.CreateSession(
        session_id=TestDefaults.SESSION_ID, user_id=TestDefaults.USER_ID
    )


@pytest.fixture(scope="module")
def session_created():
    return model.SessionCreated(
        session_id=TestDefaults.SESSION_ID,
        user_id=TestDefaults.USER_ID,
        session_name="New Session",
    )


def test_create_user_via_command(create_user: model.CreateUser):
    # TODO: we should not create user actor
    user = model.User.create(create_user)
    assert isinstance(user, model.User)
    assert user.entity_id == create_user.entity_id


def test_rebuild_user_by_events(
    user_created: model.UserCreated, session_created: model.SessionCreated
):
    user: model.User = model.User.apply(user_created)
    user.apply(session_created)

    assert isinstance(user, model.User)
    assert user.entity_id == user_created.entity_id
    assert session_created.session_id in user.session_ids


# def test_user_password(user_info: model.UserInfo):
#     assert encrypt.verify_password(
#         TestDefaults.USER_PASSWORD.encode(), user_info.hash_password
#     )
