import typing as ty

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app.auth.errors import UserAlreadyExistError
from src.app.auth.repository import UserRepository
from src.app.auth.service import Authenticator, AuthService
from src.domain.config import Settings
from src.domain.model.test_default import TestDefaults
from src.infra.cache import MemoryCache
from src.infra.encrypt import TokenEncrypt
from src.infra.mq import MessageProducer


@pytest.fixture(scope="module")
async def auth_service(
    async_engine: AsyncEngine,
    local_cache: MemoryCache[str, str],
    settings: Settings,
    token_encrypt: TokenEncrypt,
    producer: MessageProducer[ty.Any],
):
    return AuthService(
        UserRepository(async_engine),
        Authenticator(
            token_cache=local_cache,
            token_encrypt=token_encrypt,
            token_ttl=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
        producer=producer,
    )


async def test_create_user(test_defaults: TestDefaults, auth_service: AuthService):
    await auth_service.signup_user(
        test_defaults.USER_NAME, test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    user = await auth_service.find_user(useremail=test_defaults.USER_EMAIL)
    assert user
    assert user.user_info.user_name == test_defaults.USER_NAME
    assert user.user_info.user_email == test_defaults.USER_EMAIL
    assert user.role == "user"


async def test_create_user_with_empty_email(
    test_defaults: TestDefaults, auth_service: AuthService
):
    with pytest.raises(UserAlreadyExistError):
        await auth_service.signup_user(
            test_defaults.USER_NAME,
            test_defaults.USER_EMAIL,
            test_defaults.USER_PASSWORD,
        )


async def test_user_login(test_defaults: TestDefaults, auth_service: AuthService):
    token = await auth_service.login(
        test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    assert await auth_service.is_user_authenticated(token)
