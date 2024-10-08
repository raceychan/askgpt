import pytest
from tests.conftest import TestDefaults

from askgpt.app.auth import *


async def test_create_user(
    test_defaults: TestDefaults, auth_service: service.AuthService
):
    await auth_service.signup_user(
        test_defaults.USER_NAME, test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    user = await auth_service.find_user(email=test_defaults.USER_EMAIL)
    assert user
    assert user.credential.user_name == test_defaults.USER_NAME
    assert user.credential.user_email == test_defaults.USER_EMAIL
    assert user.role == "user"


async def test_create_user_with_existing_email(
    test_defaults: TestDefaults, auth_service: service.AuthService
):
    with pytest.raises(errors.UserAlreadyExistError):
        await auth_service.signup_user(
            test_defaults.USER_NAME,
            test_defaults.USER_EMAIL,
            test_defaults.USER_PASSWORD,
        )


async def test_user_login(
    test_defaults: TestDefaults, auth_service: service.AuthService
):
    token = await auth_service.login(
        test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    assert token


async def test_user_login_fail(
    test_defaults: TestDefaults, auth_service: service.AuthService
):
    randon_psw = "random_psw"
    with pytest.raises(errors.InvalidPasswordError):
        await auth_service.login(test_defaults.USER_EMAIL, randon_psw)


async def test_get_user_and_login(
    test_defaults: TestDefaults, auth_service: service.AuthService
):
    token = await auth_service.login(
        test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    jwt = auth_service._encryptor.decrypt_jwt(token)
    token = model.AccessToken.model_validate(jwt)
    user = await auth_service.get_user(token.sub)
    assert isinstance(user, model.UserAuth)
