import pytest

from askgpt.app.auth._errors import InvalidPasswordError, UserAlreadyExistError
from askgpt.app.auth.service import AuthService
from askgpt.app.user.service import UserService
from tests.conftest import UserDefaults


async def test_create_user(
    test_defaults: UserDefaults, auth_service: AuthService, user_service: UserService
):
    await auth_service.signup_user(
        test_defaults.USER_NAME, test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    user = await user_service.find_user(email=test_defaults.USER_EMAIL)
    assert user
    assert user.name == test_defaults.USER_NAME
    assert user.email == test_defaults.USER_EMAIL


async def test_create_user_with_existing_email(
    test_defaults: UserDefaults, auth_service: AuthService
):
    with pytest.raises(UserAlreadyExistError):
        await auth_service.signup_user(
            test_defaults.USER_NAME,
            test_defaults.USER_EMAIL,
            test_defaults.USER_PASSWORD,
        )


async def test_user_login(test_defaults: UserDefaults, auth_service: AuthService):
    token = await auth_service.login(
        test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    assert token


async def test_user_login_fail(test_defaults: UserDefaults, auth_service: AuthService):
    randon_psw = "random_psw"
    with pytest.raises(InvalidPasswordError):
        await auth_service.login(test_defaults.USER_EMAIL, randon_psw)


async def test_get_user_and_login(
    test_defaults: UserDefaults,
    auth_service: AuthService,
    user_service: UserService,
):
    token = await auth_service.login(
        test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    token = auth_service.decrypt_access_token(token)
    user = await user_service.get_user(token.sub)
    assert user
    assert user.name == test_defaults.USER_NAME
    assert user.email == test_defaults.USER_EMAIL
