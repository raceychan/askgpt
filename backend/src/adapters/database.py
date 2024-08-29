import types
import typing as ty
from contextlib import asynccontextmanager

from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.sql import Executable, text
from src.helpers.extratypes import StrDict
from src.helpers.timeutils import timeit


class AsyncDatabase:
    def __init__(self, aioengine: AsyncEngine):
        self._aioengine = aioengine

    @property
    def url(self):
        return self._aioengine.url

    @timeit
    async def execute(
        self,
        query: str | Executable,
        parameters: StrDict | None = None,
        execution_options: StrDict | None = None,
    ) -> CursorResult[ty.Any]:
        # TODO: log slow queries
        if isinstance(query, str):
            query = text(query)

        async with self._aioengine.begin() as connection:
            cursor = await connection.execute(
                query, parameters, execution_options=execution_options
            )
            return cursor

    @asynccontextmanager
    async def begin(self) -> ty.AsyncGenerator[AsyncConnection, None]:
        async with self.connect() as conn:
            async with conn.begin():
                yield conn

    def connect(self) -> AsyncConnection:
        return self._aioengine.connect()

    async def close(self) -> None:
        await self._aioengine.dispose()

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        await self.close()
