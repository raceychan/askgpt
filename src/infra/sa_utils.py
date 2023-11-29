import typing as ty
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio

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


@lru_cache(maxsize=1)
def async_engine_factory(
    db_url: str,
    *,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    # NOTE: NullPool is incompatible with sqlite(:memory:), wiht it every connection creates a new db
    poolclass: type[sa.Pool] | None = None,
    execution_options: dict[str, ty.Any] | None = None,
    isolation_level: sa.engine.interfaces.IsolationLevel = "READ COMMITTED",
) -> sa_aio.AsyncEngine:
    """
    lru-cached async engine factory
    """
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


@lru_cache(maxsize=1)
def engine_factory(
    db_url: str,
    *,
    echo: bool | ty.Literal["debug"] = False,
    hide_parameters: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    poolclass: type[sa.Pool] | None = None,
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


class SQLDebugger:
    def __init__(self, engine: sa.Engine):
        self.engine = engine
        self.inspector = sa.inspect(engine)

    def execute(self, sql: str) -> list[dict[str, ty.Any]]:
        import rich

        with self.engine.begin() as conn:
            rich.print(f"{self} is executing sql=:\n {sql}\n")
            res = conn.execute(sa.text(sql))
            rows = res.all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def build(cls, db_url: str):
        engine = engine_factory(db_url, isolation_level="SERIALIZABLE", echo=True)
        return cls(engine)

    def __str__(self):
        return f"{self.__class__.__name__}({self.engine.url})"

    def __call__(self, sql: str) -> list[dict[str, ty.Any]]:
        return self.execute(sql)

    @property
    def tables(self):
        return self.inspector.get_table_names()

    @classmethod
    def from_async_engine(cls, async_engine: sa_aio.AsyncEngine):
        url = str(async_engine.url).replace("+aiosqlite", "")
        return cls.build(url)


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
        res = await cursor.execute(sa.text(sql))
        row = res.one()

    return dict(row._mapping)
