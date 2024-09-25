import typing as ty

import pytest
from tests.conftest import TestDefaults

from askgpt.adapters.cache import MemoryCache
from askgpt.adapters.database import AsyncDatabase
from askgpt.adapters.queue import MessageProducer
from askgpt.app.auth.errors import UserAlreadyExistError
from askgpt.app.auth.repository import UserRepository
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.domain.config import Settings
from askgpt.infra.security import Encrypt


@pytest.fixture(scope="module")
async def auth_service(
    aiodb: AsyncDatabase,
    local_cache: MemoryCache[str, str],
    settings: Settings,
    token_encrypt: Encrypt,
    producer: MessageProducer[ty.Any],
):
    keyspace = settings.redis.keyspaces.APP.add_cls(TokenRegistry)

    return AuthService(
        user_repo=UserRepository(aiodb),
        token_encrypt=token_encrypt,
        token_registry=TokenRegistry(
            token_cache=local_cache,
            keyspace=keyspace,
        ),
        producer=producer,
        security_settings=settings.security,
    )


async def test_create_user(test_defaults: TestDefaults, auth_service: AuthService):
    await auth_service.signup_user(
        test_defaults.USER_NAME, test_defaults.USER_EMAIL, test_defaults.USER_PASSWORD
    )
    user = await auth_service.find_user(email=test_defaults.USER_EMAIL)
    assert user
    assert user.credential.user_name == test_defaults.USER_NAME
    assert user.credential.user_email == test_defaults.USER_EMAIL
    assert user.role == "user"


async def test_create_user_with_existing_email(
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
    assert token
