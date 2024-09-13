import pytest
from src.domain.model import user
from src.infra import security
from tests.conftest import TestDefaults


@pytest.fixture(scope="package")
def user_info(test_defaults: TestDefaults):
    e = test_defaults.USER_INFO
    assert security.verify_password(
        test_defaults.USER_PASSWORD.encode(), e.hash_password
    )

    return e


@pytest.fixture(scope="package")
def user_created(test_defaults: TestDefaults):  # , user_info: model.UserInfo):
    return user.UserCreated(user_id=test_defaults.USER_ID)  # user_info=user_info)
