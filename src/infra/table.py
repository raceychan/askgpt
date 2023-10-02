import typing as ty
import sqlalchemy as sa
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.sql import type_api as sa_ty


def as_sa_types(py_type: type) -> sa_ty.TypeEngine:
    import datetime
    import uuid
    import decimal

    TYPES_MAPPING = {
        str: sa.String,
        int: sa.Integer,
        datetime.datetime: sa.DateTime,
        bool: sa.Boolean,
        float: sa.Float,
        list: sa.JSON,
        dict: sa.JSON,
        uuid.UUID: sa.UUID,
        None: sa.Null,
        decimal.Decimal: sa.Numeric,
    }

    return TYPES_MAPPING[py_type]


EVENT_TABLE: ty.Final[sa.TableClause] = sa.table(
    "domain_events",
    sa.column("id", sa.String),
    sa.column("event_type", sa.String),
    sa.column("event_body", sa.JSON),
    sa.column("entity_id", sa.String),
    sa.column("version", sa.String),
    sa.column("gmt_modified", sa.DateTime),
)


async def create_table(engine: sa_aio.AsyncEngine):
    from sqlalchemy.orm import registry

    mapper_registry = registry()

    meta_data = mapper_registry.metadata
    EVENT_SCHEMA = sa.Table(
        "domain_events",
        meta_data,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("event_type", sa.String, index=True),
        sa.Column("event_body", sa.JSON),
        sa.Column("entity_id", sa.String, index=True),
        sa.Column("version", sa.String, index=True),
        sa.Column("gmt_modified", sa.DateTime),
    )

    async with engine.begin() as conn:
        await conn.run_sync(EVENT_SCHEMA.metadata.create_all)
