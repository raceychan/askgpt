from sqlalchemy.ext import asyncio as sa_aio

from src.app.gpt.model import ISessionRepository


class SessionRepository(ISessionRepository):
    def __init__(self, aioengine: sa_aio.AsyncEngine):
        self._aioengine = aioengine

    @property
    def aioengine(self) -> sa_aio.AsyncEngine:
        return self._aioengine
