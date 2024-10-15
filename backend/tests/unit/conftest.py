import pytest
from tests.conftest import UserDefaults

from askgpt.app.gpt.model import UserCreated
from askgpt.infra import security


@pytest.fixture(scope="package")
def user_info(test_defaults: UserDefaults):
    e = test_defaults.USER_INFO
    assert security.verify_password(
        test_defaults.USER_PASSWORD.encode(), e.hash_password
    )

    return e


@pytest.fixture(scope="package")
def user_created(test_defaults: UserDefaults):  # , user_info: model.UserInfo):
    return UserCreated(user_id=test_defaults.USER_ID)
