import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from src.app.auth.repository import (
    UserAuth,
    UserRepository,
    dump_userauth,
    load_userauth,
)


@pytest.fixture(scope="module")
def user_repo(async_engine: AsyncEngine):
    return UserRepository(async_engine)


def test_deserialzie(user_auth: UserAuth):
    assert load_userauth(dump_userauth(user_auth)) == user_auth


async def test_add_user(user_auth: UserAuth, user_repo: UserRepository):
    await user_repo.add(user_auth)


async def test_get_user(user_auth: UserAuth, user_repo: UserRepository):
    user = await user_repo.get(user_auth.entity_id)
    assert user == user_auth


async def test_user_unique_email(user_auth: UserAuth, user_repo: UserRepository):
    with pytest.raises(Exception):
        await user_repo.add(user_auth)
        await user_repo.add(user_auth)


async def test_search_user_by_email(user_auth: UserAuth, user_repo: UserRepository):
    user = await user_repo.search_user_by_email(user_auth.user_info.user_email)
    assert user == user_auth
