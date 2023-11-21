import pytest

from src.app.gpt import model
from src.domain import encrypt


@pytest.fixture(scope="package")
def user_info():
    e = model.TestDefaults.USER_INFO
    assert encrypt.verify_password(model.TestDefaults.USER_PASSWORD, e.hash_password)

    return e


@pytest.fixture(scope="package")
def user_created(user_info: model.UserInfo):
    return model.UserCreated(user_id=model.TestDefaults.USER_ID, user_info=user_info)
