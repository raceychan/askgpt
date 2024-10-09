import types
import typing as ty
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncConnection

from askgpt.adapters.database import (
    AsyncDatabase,
    Executable,
    ExecutionOptions,
    StrMap,
    text,
)
from askgpt.domain.errors import GeneralWebError


class LostContextError(GeneralWebError):
    def __init__(self, msg: str = ""):
        msg = msg or "Connection is used without entering UnitOfWork context"
        super().__init__(msg)


class UnitOfWork:
    """
    Unit of Work pattern implementation to manage database connections using ContextVar,
    ensuring that each coroutine gets its own connection.

    This approach prevents shared connections across different async tasks, similar to
    a transaction scope in .NET.
    """

    def __init__(self, aiodb: AsyncDatabase):
        self._aiodb = aiodb
        self._connection_context = ContextVar[AsyncConnection]("connection_context")

    @property
    def conn(self) -> AsyncConnection:
        """Return the current connection for this coroutine."""
        try:
            _conn = self._connection_context.get()
        except LookupError:
            raise LostContextError()
        return _conn

    async def execute(
        self,
        query: str | Executable,
        *,
        parameters: StrMap | ty.Sequence[StrMap] | None = None,
        execution_options: StrMap | ExecutionOptions | None = None,
    ):
        if isinstance(query, str):
            query = text(query)
        return await self.conn.execute(
            statement=query,
            parameters=parameters,
            execution_options=execution_options,
        )

    async def __aenter__(self):
        self._transaction = self._aiodb.begin()
        connection = await self._transaction.__aenter__()
        self._connection_token = self._connection_context.set(connection)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        await self._transaction.__aexit__(exc_type, exc_val, exc_tb)
        self._connection_context.reset(self._connection_token)
