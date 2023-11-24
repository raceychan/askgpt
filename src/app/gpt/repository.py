import json
import typing as ty

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

from src.app.gpt.model import ISessionRepository, IUserRepository, User


def user_deserializer(user_data: dict[str, ty.Any]) -> User:
    user_id: str = user_data["entity_id"]
    event_body: str = user_data["event_body"]
    user_info = json.loads(event_body)["user_info"]
    return User(user_id=user_id, user_info=user_info)


class UserRepository(IUserRepository):
    def __init__(self, aioengine: sa_aio.AsyncEngine):
        self._aioengine = aioengine

    async def add(self, entity: User) -> None:
        ...

    async def get(self, entity_id: str) -> User:
        ...

    @property
    def aioengine(self) -> sa_aio.AsyncEngine:
        return self._aioengine

    async def search_user_by_email(self, useremail: str) -> User | None:
        sql = """
        SELECT 
            * 
        FROM 
            domain_events 
        WHERE 
            event_body->>'user_info'->>'user_email' = :useremail
        """
        stmt = sa.text(sql).bindparams(useremail=useremail)

        async with self.aioengine.begin() as conn:
            cursor = await conn.execute(stmt)
            res = cursor.one_or_none()

        if not res:
            return None

        user_data = dict(res._mapping)  # type: ignore
        return user_deserializer(user_data)


class SessionRepository(ISessionRepository):
    def __init__(self, aioengine: sa_aio.AsyncEngine):
        self._aioengine = aioengine
