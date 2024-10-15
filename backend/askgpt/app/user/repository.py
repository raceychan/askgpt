import typing as ty

from sqlalchemy import RowMapping, insert, select, update

from askgpt.app.user.model import UserInfo
from askgpt.infra.schema import UserSchema
from askgpt.infra.uow import UnitOfWork


def load_user(user: RowMapping) -> UserInfo:
    return UserInfo(entity_id=user.id, email=user.email, name=user.username)


class UserRepository:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    @property
    def uow(self):
        return self._uow

    async def get(self, user_id: str) -> UserInfo | None:
        async with self._uow.trans():
            stmt = select(UserSchema).where(UserSchema.id == user_id)
            cursor = await self._uow.execute(stmt)
            row = cursor.mappings().one_or_none()
            if not row:
                return None
            return load_user(row)

    async def search_user_by_email(self, email: str) -> UserInfo | None:
        async with self._uow.trans():
            stmt = select(UserSchema).where(UserSchema.email == email)
            cursor = await self._uow.execute(stmt)
            row = cursor.mappings().one_or_none()
            if not row:
                return None
            return load_user(row)

    async def remove(self, user_id: str) -> None:
        async with self._uow.trans():
            stmt = (
                update(UserSchema)
                .where(UserSchema.id == user_id)
                .values(is_active=False)
            )
            await self._uow.execute(stmt)

    async def add(self, user: UserInfo) -> None:
        async with self._uow.trans():
            stmt = insert(UserSchema).values(
                id=user.entity_id,
                email=user.email,
                username=user.name,
            )
            await self._uow.execute(stmt)

    async def update(self, user: UserInfo, values: dict[str, ty.Any]) -> None:
        async with self._uow.trans():
            stmt = (
                update(UserSchema)
                .where(UserSchema.id == user.entity_id)
                .values(**values)
            )
            await self._uow.execute(stmt)
