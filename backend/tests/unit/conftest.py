import pytest

from src.app.gpt import model
from src.domain.model.test_default import TestDefaults
from src.infra import encrypt


@pytest.fixture(scope="package")
def user_info(test_defaults: TestDefaults):
    e = test_defaults.USER_INFO
    assert encrypt.verify_password(
        test_defaults.USER_PASSWORD.encode(), e.hash_password
    )

    return e


@pytest.fixture(scope="package")
def user_created(test_defaults: TestDefaults):  # , user_info: model.UserInfo):
    return model.UserCreated(user_id=test_defaults.USER_ID)  # user_info=user_info)
