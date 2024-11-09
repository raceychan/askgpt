import sqlalchemy as sa
from askgpt.helpers.sql import UnitOfWork
from askgpt.infra.schema import SessionsTable

from ._model import ChatSession, ISessionRepository


def session_from_row(row: sa.RowMapping) -> ChatSession:
    return ChatSession(
        session_id=row.id, user_id=row.user_id, session_name=row.session_name
    )


from askgpt.domain.config import dg


class SessionRepository(ISessionRepository):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    @property
    def uow(self) -> UnitOfWork:
        return self._uow

    async def list_sessions(self, user_id: str) -> list[ChatSession]:
        stmt = sa.select(SessionsTable).where(SessionsTable.user_id == user_id)
        cursor = await self._uow.execute(stmt)
        rows = cursor.mappings().all()
        return [session_from_row(row) for row in rows]

    async def add(self, entity: ChatSession):
        stmt = sa.insert(SessionsTable).values(
            id=entity.entity_id,
            user_id=entity.user_id,
            session_name=entity.session_name,
        )

        await self._uow.execute(stmt)

    async def rename(self, entity: ChatSession):
        stmt = (
            sa.update(SessionsTable)
            .where(SessionsTable.id == entity.entity_id)
            .values(session_name=entity.session_name)
        )
        await self._uow.execute(stmt)

    async def remove(self, entity_id: str):
        stmt = sa.delete(SessionsTable).where(SessionsTable.id == entity_id)
        await self._uow.execute(stmt)

    async def get(self, entity_id: str) -> ChatSession | None:
        stmt = sa.select(SessionsTable).where(SessionsTable.id == entity_id)
        cursor = await self._uow.execute(stmt)
        row = cursor.mappings().one_or_none()
        if not row:
            return None
        return session_from_row(row)

    async def get_user_session(self, entity_id: str) -> ChatSession | None:
        stmt = sa.select(SessionsTable).where(SessionsTable.id == entity_id)
        cursor = await self._uow.execute(stmt)
        row = cursor.mappings().one_or_none()
        if not row:
            return None
        return session_from_row(row)
