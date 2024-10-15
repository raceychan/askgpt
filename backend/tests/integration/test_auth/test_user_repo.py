import pytest

from askgpt.app.auth.repository import (
    AuthRepository,
    UserAuth,
    dump_userauth,
    load_userauth,
)
from askgpt.adapters.uow import UnitOfWork


@pytest.fixture(scope="module")
def user_repo(uow: UnitOfWork):
    return AuthRepository(uow)


def test_deserialzie(user_auth: UserAuth):
    assert load_userauth(dump_userauth(user_auth)) == user_auth


async def test_add_user(user_auth: UserAuth, user_repo: AuthRepository):
    async with user_repo.uow.trans():
        await user_repo.add(user_auth)


async def test_get_user(user_auth: UserAuth, user_repo: AuthRepository):
    async with user_repo.uow.trans():
        user = await user_repo.get(user_auth.entity_id)
    assert user == user_auth


async def test_user_unique_email(user_auth: UserAuth, user_repo: AuthRepository):
    with pytest.raises(Exception):
        async with user_repo.uow.trans():
            await user_repo.add(user_auth)
            await user_repo.add(user_auth)


async def test_search_user_by_email(user_auth: UserAuth, user_repo: AuthRepository):
    async with user_repo.uow.trans():
        user = await user_repo.search_user_by_email(user_auth.credential.user_email)
    assert user == user_auth
