import typing as ty

import sqlalchemy as sa
from askgpt.adapters.database import AsyncDatabase
from askgpt.app.gpt.model import ChatSession, ISessionRepository

SESSION_TABLE: ty.Final[sa.TableClause] = sa.table(
    "sessions",
    sa.column("id", sa.String),
    sa.column("user_id", sa.String),
    sa.column("session_name", sa.String),
    sa.column("gmt_modified", sa.DateTime),
    sa.column("gmt_created", sa.DateTime),
)


# def entity_loader(row: sa.engine.Row) -> ChatSession:
#     ...


class SessionRepository(ISessionRepository):
    def __init__(self, aiodb: AsyncDatabase):
        self._aiodb = aiodb

    @property
    def aiodb(self) -> AsyncDatabase:
        return self._aiodb

    async def list_sessions(self, user_id: str) -> list[ChatSession]:
        stmt = sa.select(SESSION_TABLE).where(SESSION_TABLE.c.user_id == user_id)
        cursor = await self._aiodb.execute(stmt)
        rows = cursor.fetchall()
        sessions = [
            ChatSession(
                session_id=row.id, user_id=row.user_id, session_name=row.session_name
            )
            for row in rows
        ]
        return sessions

    async def add(self, entity: ChatSession):
        stmt = sa.insert(SESSION_TABLE).values(
            id=entity.entity_id,
            user_id=entity.user_id,
            session_name=entity.session_name,
        )

        await self._aiodb.execute(stmt)

    async def rename(self, entity: ChatSession):
        stmt = (
            sa.update(SESSION_TABLE)
            .where(SESSION_TABLE.c.id == entity.entity_id)
            .values(session_name=entity.session_name)
        )
        await self._aiodb.execute(stmt)

    async def remove(self, session_id: str):
        stmt = sa.delete(SESSION_TABLE).where(SESSION_TABLE.c.id == session_id)
        await self._aiodb.execute(stmt)

    async def get(self, entity_id: str) -> ChatSession | None:
        stmt = sa.select(SESSION_TABLE).where(SESSION_TABLE.c.id == entity_id)
        cursor = await self._aiodb.execute(stmt)
        row = cursor.one_or_none()
        if not row:
            return None
        return ChatSession(
            session_id=row.id, user_id=row.user_id, session_name=row.session_name
        )
