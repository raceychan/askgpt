import types
import typing as ty
from contextlib import asynccontextmanager

from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.sql import Executable, text

from askgpt.helpers._log import logger
from askgpt.helpers.time import timeit

type StrMap = ty.Mapping[str, ty.Any]
type SQL_ISOLATIONLEVEL = ty.Literal[
    "SERIALIZABLE",
    "REPEATABLE READ",
    "READ COMMITTED",
    "READ UNCOMMITTED",
    "AUTOCOMMIT",
]


class ExecutionOptions(ty.TypedDict, total=False):
    """
    reff: https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection.execution_options
    """

    compiled_cache: dict[str, ty.Any]
    logging_token: str
    isolation_level: SQL_ISOLATIONLEVEL
    no_parameters: bool
    stream_results: bool
    max_row_buffer: int
    yield_per: int
    insertmanyvalues_page_size: int
    schema_translate_map: dict[str | None, str | None] | None
    preserve_rowcount: bool


class ExecuteParams(ty.TypedDict):
    query: str | Executable
    parameters: StrMap | ty.Sequence[StrMap] | None
    execution_options: StrMap | ExecutionOptions | None


class AsyncDatabase:
    def __init__(self, aioengine: AsyncEngine):
        self._aioengine = aioengine

    @property
    def url(self):
        return self._aioengine.url

    @timeit(logger=logger)
    async def execute(
        self,
        query: str | Executable,
        *,
        parameters: StrMap | ty.Sequence[StrMap] | None = None,
        execution_options: StrMap | ExecutionOptions | None = None,
    ) -> CursorResult[ty.Any]:
        if isinstance(query, str):
            query = text(query)

        async with self._aioengine.connect() as connection:
            cursor = await connection.execute(
                query, parameters, execution_options=execution_options
            )
            return cursor

    @asynccontextmanager
    async def begin(self) -> ty.AsyncGenerator[AsyncConnection, None]:
        async with self.connect() as conn:
            async with conn.begin():
                yield conn

    @timeit(logger=logger)
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
