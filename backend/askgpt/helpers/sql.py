import typing as ty
from contextlib import contextmanager

import sqlalchemy as sa
from askgpt.helpers.string import str_to_snake
from sqlalchemy import MetaData
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import FromClause, func


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
