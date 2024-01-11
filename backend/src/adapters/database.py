import typing as ty
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction
from sqlalchemy.sql import Executable, text


class AsyncDatabase:
    def __init__(self, aioengine: AsyncEngine):
        self._aioengine = aioengine

    @property
    def url(self):
        return self._aioengine.url

    async def execute(
        self,
        query: str | Executable,
        parameters: dict | None = None,
        execution_options: dict | None = None,
    ) -> ty.Any:
        # TODO: log slow queries
        if isinstance(query, str):
            query = text(query)

        async with self._aioengine.connect() as connection:
            result = await connection.execute(
                query, parameters, execution_options=execution_options
            )
            return result

    @asynccontextmanager
    async def begin(self) -> ty.AsyncGenerator[AsyncTransaction, None]:
        async with self.connect() as conn:
            async with conn.begin() as transaction:
                yield transaction

    @asynccontextmanager
    async def connect(self) -> ty.AsyncGenerator[AsyncConnection, None]:
        async with self._aioengine.connect() as conn:
            yield conn

    async def close(self):
        await self._aioengine.dispose()

    async def __aenter__(self):
        await self.execute("select 1")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
