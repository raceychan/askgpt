import sqlalchemy as sa
from sqlalchemy import orm as sa_orm
from sqlalchemy.ext import asyncio as sa_aio
from sqlalchemy.sql import func
from src.tools.nameutils import str_to_snake


# Reference: https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html
def declarative[T](cls: type[T]) -> type[T]:
    """
    A more pythonic way to declare a sqlalchemy table
    """

    return sa_orm.declarative_base(cls=cls)  # type: ignore


@declarative
class TableBase:
    """
    Representation of actual tables in database,
    used for DDL and data migrations only
    """

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


class EventSchema(TableBase):
    __tablename__: str = "domain_events"  # type: ignore

    id = sa.Column("id", sa.String, primary_key=True)
    event_type = sa.Column("event_type", sa.String, index=True)
    event_body = sa.Column("event_body", sa.JSON)
    entity_id = sa.Column("entity_id", sa.String, index=True)
    version = sa.Column("version", sa.String, index=True)


class UserSchema(TableBase):
    __tablename__: str = "users"  # type: ignore

    id = sa.Column("id", sa.String, primary_key=True)
    username = sa.Column("username", sa.String, unique=False, index=True)
    email = sa.Column("email", sa.String, unique=True, index=True)
    password_hash = sa.Column("password_hash", sa.String, nullable=False)
    last_login = sa.Column("last_login", sa.DateTime, nullable=True)
    role = sa.Column("role", sa.String, nullable=False)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class SessionSchema(TableBase):
    __tablename__: str = "sessions"  # type: ignore

    id = sa.Column("id", sa.String, primary_key=True)
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    session_id = sa.Column("session_id", sa.String, unique=True, index=True)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class UserAPIKeySchema(TableBase):
    __tablename__: str = "user_api_keys"  # type: ignore
    __table_args__ = (
        sa.UniqueConstraint("user_id", "api_key", name="user_api_key_unique"),
    )

    id = sa.Column("id", sa.Integer, autoincrement=True, primary_key=True)
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    api_type = sa.Column("api_type", sa.String, index=True)
    api_key = sa.Column("api_key", sa.String, unique=True, index=True)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


async def create_tables(engine: sa_aio.AsyncEngine):
    # tables = TableBase.metadata.tables.keys()

    async with engine.begin() as conn:
        await conn.run_sync(TableBase.metadata.create_all)
