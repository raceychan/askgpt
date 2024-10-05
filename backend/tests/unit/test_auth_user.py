import pytest
from tests.conftest import TestDefaults

from askgpt.app.auth.model import UserAuth
from askgpt.domain.model.base import utc_now


@pytest.fixture(scope="function")
def user_auth(test_defaults: TestDefaults) -> UserAuth:
    return UserAuth(
        credential=test_defaults.USER_INFO,
        user_id=test_defaults.USER_ID,
        last_login=utc_now(),
    )


def test_user_promote(user_auth: UserAuth):
    assert user_auth.is_admin is False
    user_auth.promote_to_admin()
    assert user_auth.is_admin is True


def test_user_deactivate(user_auth: UserAuth):
    assert user_auth.is_active is True
    user_auth.deactivate()
    assert user_auth.is_active is False


def test_user_login(user_auth: UserAuth):
    assert user_auth.last_login is not None
    last_login = user_auth.last_login
    user_auth.login()
    assert user_auth.last_login > last_login
