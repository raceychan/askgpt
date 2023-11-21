import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.sql import func

from src.domain.model.name_tools import str_to_snake
from src.infra.sa_utils import test_table_exist


def declarative[T](cls: type[T]) -> type[T]:
    # Reference: https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html
    return sa_orm.declarative_base(cls=cls)  # type: ignore


@declarative
class TableBase:
    gmt_modified = sa.Column("gmt_modified", sa.DateTime, onupdate=func.now())
    gmt_created = sa.Column("gmt_created", sa.DateTime, server_default=func.now())

    @sa_orm.declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return str_to_snake(cls.__name__)

    @classmethod
    def create_table(cls, engine: sa.Engine) -> None:
        cls.metadata.create_all(engine)  # type: ignore

    @classmethod
    async def create_table_async(cls, async_engine: sa_aio.AsyncEngine) -> None:
        async with async_engine.begin() as conn:
            await conn.run_sync(cls.metadata.create_all)  # type:ignore

    @classmethod
    def generate_tableclause(cls) -> sa.TableClause:
        clause = sa.table(
            cls.__tablename__,
            *[sa.column(c) for c in cls.__table__.columns],  # type: ignore
        )
        return clause

    @classmethod
    async def assure_table_exist(cls, engine: sa_aio.AsyncEngine) -> bool:
        row = await test_table_exist(engine, cls.__tablename__)
        if cls.__tablename__ == row["name"]:
            return True
        raise Exception(f"Table {cls.__tablename__} does not exist")


class EventSchema(TableBase):
    """
    This should be our single source of truth for table
    """

    id = sa.Column("id", sa.String, primary_key=True)

    __tablename__: str = "domain_events"  # type: ignore

    event_type = sa.Column("event_type", sa.String, index=True)
    event_body = sa.Column("event_body", sa.JSON)
    entity_id = sa.Column("entity_id", sa.String, index=True)
    version = sa.Column("version", sa.String, index=True)


class UserSchema(TableBase):
    __tablename__: str = "users"  # type: ignore

    id = sa.Column("id", sa.Integer, primary_key=True, autoincrement="auto")
    username = sa.Column("username", sa.String, unique=True, index=True)
    email = sa.Column("email", sa.String, unique=True, index=True)
    password_hash = sa.Column("password_hash", sa.String)
    last_login = sa.Column("last_login", sa.DateTime, nullable=True)
    is_active = sa.Column("is_active", sa.Boolean, default=True)
    is_admin = sa.Column("is_admin", sa.Boolean, default=False)
