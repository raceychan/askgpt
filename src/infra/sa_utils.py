import typing as ty

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

# from sqlalchemy.sql import type_api as sa_ty


# def as_sa_types(py_type: type) -> type:
#     import datetime
#     import decimal
#     import uuid

#     TYPES_MAPPING = {
#         str: sa.String,
#         int: sa.Integer,
#         datetime.datetime: sa.DateTime,
#         bool: sa.Boolean,
#         float: sa.Float,
#         list: sa.JSON,
#         dict: sa.JSON,
#         uuid.UUID: sa.UUID,
#         None: sa.Null,
#         decimal.Decimal: sa.Numeric,
#     }

#     return TYPES_MAPPING[py_type]


def async_engine_factory(
    db_url: str,
    *,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    poolclass: type[sa.Pool]
    | None = None,  # = sa.NullPool, NullPool is incompatible with sqlite(:memory:), cause every connection is a new db
    execution_options: dict[str, ty.Any] | None = None,
    isolation_level: sa.engine.interfaces.IsolationLevel = "READ COMMITTED",
) -> sa_aio.AsyncEngine:
    engine = sa_aio.create_async_engine(
        db_url,
        echo=echo,
        hide_parameters=hide_parameters,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        poolclass=poolclass,
        execution_options=execution_options,
        isolation_level=isolation_level,
    )
    return engine


def engine_factory(
    db_url: str,
    *,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    poolclass: type[sa.Pool] | None = sa.NullPool,
    execution_options: dict[str, ty.Any] | None = None,
    isolation_level: sa.engine.interfaces.IsolationLevel = "READ COMMITTED",
):
    engine = sa.create_engine(
        db_url,
        echo=echo,
        hide_parameters=hide_parameters,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=pool_recycle,
        poolclass=poolclass,
        execution_options=execution_options,
        isolation_level=isolation_level,
    )
    return engine


class SQLDebuger:
    def __init__(self, engine: sa.Engine):
        self.engine = engine
        self.inspector = sa.inspect(engine)

    def execute(self, sql: str) -> list[dict[str, ty.Any]]:
        with self.engine.begin() as conn:
            result = conn.execute(sa.text(sql))
            rows = result.all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def build(cls, db_url: str):
        engine = engine_factory(db_url, isolation_level="SERIALIZABLE", echo=True)
        return cls(engine)

    def __call__(self, sql: str) -> list[dict[str, ty.Any]]:
        return self.execute(sql)

    @property
    def tables(self):
        return self.inspector.get_table_names()


async def test_table_exist(async_engine: sa_aio.AsyncEngine, tablename: str):
    sql = f"""
    SELECT 
        name 
    FROM 
        sqlite_schema 
    WHERE
        type='table' AND name='{tablename}' 
    ORDER BY 
        name
    """.strip()

    async with async_engine.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        row = cache.one()

    return dict(row._mapping)
