import typing as ty

import sqlalchemy as sa

from askgpt.app.auth.model import UserAuth, UserCredential
from askgpt.infra.schema import UserAPIKeySchema, UserSchema
from askgpt.adapters.uow import UnitOfWork


def dump_userauth(user: UserAuth) -> dict[str, ty.Any]:
    # TODO: should (instead of dict) map UserAuth to UserSchema
    return dict(
        id=user.entity_id,
        username=user.credential.user_name,
        email=user.credential.user_email,
        role=user.role,
        password_hash=user.credential.hash_password.decode(),
        last_login=user.last_login,
        is_active=user.is_active,
    )


def load_userauth(user_data: dict[str, ty.Any]) -> UserAuth:
    # TODO: should (instead of dict) map UserAuth to UserSchema
    user_info = UserCredential(
        user_name=user_data["username"],
        user_email=user_data["email"],
        hash_password=user_data["password_hash"],
    )
    return UserAuth(
        user_id=user_data["id"],
        credential=user_info,
        role=user_data["role"],
        last_login=user_data["last_login"],
    )


class AuthRepository:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    @property
    def uow(self):
        return self._uow

    async def add(self, entity: UserAuth) -> None:
        data = dump_userauth(entity)
        stmt = sa.insert(UserSchema).values(data)
        await self._uow.execute(stmt)

    async def get(self, entity_id: str) -> UserAuth | None:
        stmt = sa.select(UserSchema).where(UserSchema.id == entity_id)
        res = await self._uow.execute(stmt)
        row = res.one_or_none()
        if not row:
            return None

        return load_userauth(dict(row._mapping))

    async def remove(self, entity_id: str) -> None:
        stmt = (
            sa.update(UserSchema)
            .where(UserSchema.id == entity_id)
            .values(is_active=False)
        )
        await self._uow.execute(stmt)

    async def search_user_by_email(self, useremail: str) -> UserAuth | None:
        stmt = sa.select(UserSchema).where(UserSchema.email == useremail)

        cursor = await self._uow.execute(stmt)
        res = cursor.one_or_none()

        if not res:
            return None

        user_data = dict(res._mapping)  # type: ignore
        return load_userauth(user_data)

    async def add_api_key_for_user(
        self, user_id: str, encrypted_api_key: str, api_type: str, idem_id: str
    ) -> None:
        stmt = sa.insert(UserAPIKeySchema).values(
            user_id=user_id,
            api_key=encrypted_api_key,
            api_type=api_type,
            idem_id=idem_id,
        )

        await self._uow.execute(stmt)

    async def get_api_keys_for_user(self, user_id: str, api_type: str) -> list[bytes]:
        stmt = sa.select(UserAPIKeySchema).where(
            UserAPIKeySchema.user_id == user_id,
            UserAPIKeySchema.api_type == api_type,
        )

        cursor = await self._uow.execute(stmt)
        res = cursor.fetchall()
        encrypted_keys = [row.api_key for row in res]
        return encrypted_keys
