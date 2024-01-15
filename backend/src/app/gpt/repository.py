# from sqlalchemy.ext import asyncio as sa_aio
from src.adapters.database import AsyncDatabase
from src.app.gpt.model import ISessionRepository


class SessionRepository(ISessionRepository):
    def __init__(self, aiodb: AsyncDatabase):
        self._aiodb = aiodb

    @property
    def aiodb(self) -> AsyncDatabase:
        return self._aiodb
