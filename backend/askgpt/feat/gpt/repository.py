import sqlalchemy as sa

from askgpt.feat.gpt.model import ChatSession, ISessionRepository
from askgpt.infra.schema import SessionSchema
from askgpt.infra.uow import UnitOfWork


class SessionRepository(ISessionRepository):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    @property
    def uow(self) -> UnitOfWork:
        return self._uow

    async def list_sessions(self, user_id: str) -> list[ChatSession]:
        stmt = sa.select(SessionSchema).where(SessionSchema.user_id == user_id)
        cursor = await self._uow.execute(stmt)
        rows = cursor.fetchall()
        sessions = [
            ChatSession(
                session_id=row.id, user_id=row.user_id, session_name=row.session_name
            )
            for row in rows
        ]
        return sessions

    async def add(self, entity: ChatSession):
        stmt = sa.insert(SessionSchema).values(
            id=entity.entity_id,
            user_id=entity.user_id,
            session_name=entity.session_name,
        )

        await self._uow.execute(stmt)

    async def rename(self, entity: ChatSession):
        stmt = (
            sa.update(SessionSchema)
            .where(SessionSchema.id == entity.entity_id)
            .values(session_name=entity.session_name)
        )
        await self._uow.execute(stmt)

    async def remove(self, session_id: str):
        stmt = sa.delete(SessionSchema).where(SessionSchema.id == session_id)
        await self._uow.execute(stmt)

    async def get(self, entity_id: str) -> ChatSession | None:
        stmt = sa.select(SessionSchema).where(SessionSchema.id == entity_id)
        cursor = await self._uow.execute(stmt)
        row = cursor.one_or_none()
        if not row:
            return None
        return ChatSession(
            session_id=row.id, user_id=row.user_id, session_name=row.session_name
        )
