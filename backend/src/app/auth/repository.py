import typing as ty

import sqlalchemy as sa

# from sqlalchemy.ext import asyncio as sa_aio
from src.adapters.database import AsyncDatabase
from src.app.auth.model import IUserRepository, UserAuth, UserInfo

USER_TABLE: ty.Final[sa.TableClause] = sa.table(
    "users",
    sa.column("id", sa.String),
    sa.column("username", sa.String),
    sa.column("email", sa.String),
    sa.column("password_hash"),
    sa.column("last_login", sa.DateTime),
    sa.column("role", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("gmt_modified", sa.DateTime),
    sa.column("gmt_created", sa.DateTime),
)

USER_OPENAI_KEYS_TABLE: ty.Final[sa.TableClause] = sa.table(
    "user_api_keys",
    sa.column("id", sa.String),
    sa.column("user_id", sa.String),
    sa.column("api_key", sa.String),
    sa.column("api_type", sa.String),
    sa.column("is_active", sa.Boolean),
    sa.column("gmt_modified", sa.DateTime),
    sa.column("gmt_created", sa.DateTime),
)


def dump_userauth(user: UserAuth) -> dict[str, ty.Any]:
    data = user.asdict(by_alias=False)
    return dict(
        id=data["entity_id"],
        username=data["user_info"]["user_name"],
        email=data["user_info"]["user_email"],
        role=data["role"],
        password_hash=data["user_info"]["hash_password"],
        last_login=data["last_login"],
        is_active=data["is_active"],
    )


def load_userauth(user_data: dict[str, ty.Any]) -> UserAuth:
    user_info = UserInfo(
        user_name=user_data["username"],
        user_email=user_data["email"],
        hash_password=user_data["password_hash"],
    )
    return UserAuth(
        user_id=user_data["id"],
        user_info=user_info,
        role=user_data["role"],
        last_login=user_data["last_login"],
    )


class UserRepository(IUserRepository):
    def __init__(self, aiodb: AsyncDatabase):
        self._aiodb = aiodb

    async def add(self, entity: UserAuth) -> None:
        data = dump_userauth(entity)
        stmt = sa.insert(USER_TABLE).values(data)

        async with self._aiodb.begin() as cursor:
            await cursor.execute(stmt)

    async def get(self, entity_id: str) -> UserAuth | None:
        stmt = sa.select(USER_TABLE).where(USER_TABLE.c.id == entity_id)
        async with self._aiodb.begin() as cursor:
            res = await cursor.execute(stmt)
            row = res.one_or_none()
            if not row:
                return None
        return load_userauth(dict(row._mapping))  # type: ignore

    async def remove(self, entity_id: str) -> None:
        stmt = (
            sa.update(USER_TABLE)
            .where(USER_TABLE.c.id == entity_id)
            .values(is_active=False)
        )
        await self._aiodb.execute(stmt)

    async def search_user_by_email(self, useremail: str) -> UserAuth | None:
        stmt = sa.select(USER_TABLE).where(USER_TABLE.c.email == useremail)

        async with self._aiodb.begin() as conn:
            cursor = await conn.execute(stmt)
            res = cursor.one_or_none()

        if not res:
            return None

        user_data = dict(res._mapping)  # type: ignore
        return load_userauth(user_data)

    async def add_api_key_for_user(
        self, user_id: str, encrypted_api_key: str, api_type: str
    ) -> None:
        stmt = sa.insert(USER_OPENAI_KEYS_TABLE).values(
            user_id=user_id, api_key=encrypted_api_key, api_type=api_type
        )

        async with self._aiodb.begin() as conn:
            await conn.execute(stmt)

    async def get_api_keys_for_user(self, user_id: str, api_type: str) -> list[bytes]:
        stmt = sa.select(USER_OPENAI_KEYS_TABLE).where(
            USER_OPENAI_KEYS_TABLE.c.user_id == user_id,
            USER_OPENAI_KEYS_TABLE.c.api_type == api_type,
        )

        async with self._aiodb.begin() as conn:
            cursor = await conn.execute(stmt)
            res = cursor.fetchall()

        encrypted_keys = [row.api_key for row in res]
        return encrypted_keys
