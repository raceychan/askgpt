import typing as ty
from contextlib import asynccontextmanager
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


class OutOfContextError(GeneralWebError):
    "raised when caller tries get connection before entering uow"

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
            raise OutOfContextError()
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

    @asynccontextmanager
    async def trans(self):
        """
        An async context manager to handle the lifecycle of the UnitOfWork transaction.
        This allows for reusing the same UnitOfWork instance across multiple objects.
        """
        transaction = self._aiodb.begin()
        connection = await transaction.__aenter__()
        token = self._connection_context.set(connection)
        try:
            yield self  # Yield the current UnitOfWork instance
        finally:
            await transaction.__aexit__(None, None, None)
            self._connection_context.reset(token)
