import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app.auth.repository import UserRepository
from src.app.auth.service import Authenticator, AuthService, CreateUserRequest
from src.app.model import TestDefaults
from src.domain.config import Settings
from src.infra.cache import LocalCache


@pytest.fixture(scope="module")
def auth_service(
    async_engine: AsyncEngine, local_cache: LocalCache[str, str], settings: Settings
):
    return AuthService(
        UserRepository(async_engine),
        Authenticator(token_cache=local_cache, security=settings.security),
    )


@pytest.fixture(scope="module")
def req(test_defaults: TestDefaults) -> CreateUserRequest:
    req = CreateUserRequest(
        user_name=test_defaults.USER_NAME,
        email=test_defaults.USER_EMAIL,
        password="password",
    )
    return req


async def test_create_user(
    test_defaults: TestDefaults, req: CreateUserRequest, auth_service: AuthService
):
    await auth_service.create_user(req)
    user = await auth_service.find_user(
        username=test_defaults.USER_NAME, useremail=test_defaults.USER_EMAIL
    )
    assert user
    assert user.user_info.user_name == test_defaults.USER_NAME
    assert user.user_info.user_email == test_defaults.USER_EMAIL
    assert user.role == "user"


async def test_create_user_with_empty_email(
    test_defaults: TestDefaults, auth_service: AuthService
):
    invalid_req = CreateUserRequest(
        user_name=test_defaults.USER_NAME, email="", password="password"
    )
    with pytest.raises(ValueError):
        await auth_service.create_user(invalid_req)


async def test_user_login(test_defaults: TestDefaults, auth_service: AuthService):
    token = await auth_service.login(
        email=test_defaults.USER_EMAIL, password=test_defaults.USER_PASSWORD
    )
    assert await auth_service.is_user_authenticated(token)
