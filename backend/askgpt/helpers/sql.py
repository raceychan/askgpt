import typing as ty
from contextlib import asynccontextmanager
from contextvars import ContextVar

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Executable, FromClause, func, text

from askgpt.helpers.string import str_to_snake

type StrMap = ty.Mapping[str, ty.Any]
type SQL_ISOLATIONLEVEL = ty.Literal[
    "SERIALIZABLE",
    "REPEATABLE READ",
    "READ COMMITTED",
    "READ UNCOMMITTED",
    "AUTOCOMMIT",
]


@ty.runtime_checkable
class IEngine(ty.Protocol):
    @asynccontextmanager
    async def begin(self) -> ty.AsyncGenerator[AsyncConnection, None]: ...


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


# Reference: https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html
def declarative(cls: type) -> type[DeclarativeBase]:
    """
    A more pythonic way to declare a sqlalchemy table
    """

    return sa_orm.declarative_base(cls=cls)


def async_engine(engine: sa.Engine) -> sa_aio.AsyncEngine:
    return sa_aio.AsyncEngine(engine)


def engine_factory(
    db_url: str,
    *,
    connect_args: dict[str, ty.Any] | None = None,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    poolclass: type[sa.Pool] | None = None,
    execution_options: dict[str, ty.Any] | None = None,
    isolation_level: sa.engine.interfaces.IsolationLevel = "READ COMMITTED",
):
    extra: dict[str, ty.Any] = dict()

    if execution_options:
        extra.update(execution_options=execution_options)
    if connect_args:
        extra.update(connect_args=connect_args)

    engine = sa.create_engine(
        db_url,
        echo=echo,
        hide_parameters=hide_parameters,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        poolclass=poolclass,
        isolation_level=isolation_level,
        **extra,
    )
    return engine


@declarative
class TableBase:
    """
    Representation of actual tables in database,
    used for DDL and data migrations only
    """

    __table__: ty.ClassVar[FromClause]

    metadata: ty.ClassVar[MetaData]

    # entity_id = sa.Column("entity_id", sa.String, unique=True, nullable=False, index=True)
    gmt_modified = sa.Column(
        "gmt_modified", sa.DateTime, server_default=func.now(), onupdate=func.now()
    )
    gmt_created = sa.Column("gmt_created", sa.DateTime, server_default=func.now())

    @sa_orm.declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return str_to_snake(cls.__name__)

    @classmethod
    def create_table(cls, engine: sa.Engine) -> None:
        cls.metadata.create_all(engine)

    @classmethod
    async def create_table_async(cls, async_engine: sa_aio.AsyncEngine) -> None:
        async with async_engine.begin() as conn:
            await conn.run_sync(cls.metadata.create_all)

    @classmethod
    def generate_tableclause(cls) -> sa.TableClause:
        clause = sa.table(
            cls.__tablename__,
            *[sa.column(c.name, c.type) for c in cls.__table__.columns],
        )
        return clause


class OutOfContextError(Exception):
    "raised when caller tries get connection before entering uow"

    def __init__(self, aiodb: IEngine):
        msg = f"Connection is used without entering UnitOfWork context, using {aiodb}"
        super().__init__(msg)


class UnitOfWork:
    """
    Unit of Work pattern implementation to manage database connections using ContextVar,
    ensuring that each coroutine gets its own connection.

    This approach prevents shared connections across different async tasks, similar to a transaction scope in .NET.
    """

    def __init__(self, aiodb: IEngine):
        self._aiodb = aiodb
        self._connection_context = ContextVar[AsyncConnection]("connection_context")

    @property
    def conn(self) -> AsyncConnection:
        """Return the current connection for this coroutine."""
        try:
            _conn = self._connection_context.get()
        except LookupError as e:
            raise OutOfContextError(self._aiodb) from e
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
    async def trans(self) -> ty.AsyncGenerator[ty.Self, None]:
        """
        An async context manager to handle the lifecycle of the UnitOfWork transaction.
        This allows for reusing the same UnitOfWork instance across multiple objects.
        """
        transaction = self._aiodb.begin()
        connection = await transaction.__aenter__()
        token = self._connection_context.set(connection)
        try:
            yield self
        finally:
            await transaction.__aexit__(None, None, None)
            self._connection_context.reset(token)
