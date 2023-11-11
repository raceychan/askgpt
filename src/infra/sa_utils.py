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
