import typing as ty

import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.sql import func

from src.domain.model.name_tools import pascal_to_snake
from src.infra.sa_utils import engine_factory

T = ty.TypeVar("T")


def declarative(cls: type[T]) -> type[T]:
    # Reference: https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html
    return sa_orm.declarative_base(cls=cls)


@declarative
class TableBase:
    # __table_args__ = {"mysql_engine": "InnoDB"}

    gmt_modified = sa.Column("gmt_modified", sa.DateTime, onupdate=func.now())
    gmt_created = sa.Column("gmt_created", sa.DateTime, server_default=func.now())

    @sa_orm.declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return pascal_to_snake(cls.__name__)

    @classmethod
    def create_table(cls, engine: sa.Engine):
        cls.metadata.create_all(engine)  # type: ignore

    @classmethod
    async def create_table_async(cls, async_engine: sa_aio.AsyncEngine):
        async with async_engine.begin() as conn:
            await conn.run_sync(cls.metadata.create_all)  # type:ignore

    @classmethod
    def generate_tableclause(cls) -> sa.TableClause:
        clause = sa.table(
            cls.__tablename__,
            *[sa.column(c) for c in cls.__table__.columns],  # type: ignore
        )
        return clause


class EventSchema(TableBase):
    """
    This should be our single source of truth for table
    """

    __tablename__ = "domain_events"  # type: ignore

    id = sa.Column("id", sa.String, primary_key=True)
    event_type = sa.Column("event_type", sa.String, index=True)
    event_body = sa.Column("event_body", sa.JSON)
    entity_id = sa.Column("entity_id", sa.String, index=True)
    version = sa.Column("version", sa.String, index=True)

    @classmethod
    def from_model(cls, model):
        raise NotImplementedError


async def test_table_exists(table_name: str, async_engine: sa_aio.AsyncEngine):
    sql = f"SELECT name FROM sqlite_schema WHERE type='table' and name='{table_name}' ORDER BY name"
    async with async_engine.begin() as cursor:
        cache = await cursor.execute(sa.text(sql))
        result = cache.one_or_none()

    if result != table_name:
        raise ValueError(f"Table {table_name} does not exist")


async def create_eventstore(async_engine: sa_aio.AsyncEngine):
    await EventSchema.create_table_async(async_engine)


async def setup_eventstore(settings):
    if settings.db.DB_DRIVER == "sqlite":
        if not settings.db.DATABASE.exists():
            raise FileNotFoundError(
                f"Database file not found at {settings.db.DATABASE}"
            )

    engine = engine_factory(settings.db.ASYNC_DB_URL, isolation_level="SERIALIZABLE")

    try:
        await test_table_exists(EventSchema.__tablename__, engine)
    except ValueError:
        await create_eventstore(engine)
