import sqlalchemy as sa

from askgpt.adapters.database import AsyncDatabase
from askgpt.helpers.sql import TableBase


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

    id = sa.Column("id", sa.String, primary_key=True, comment="session_id")
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    session_name = sa.Column("session_name", sa.String, unique=False, index=False)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class UserAPIKeySchema(TableBase):
    __tablename__: str = "user_api_keys"  # type: ignore
    __table_args__ = (
        sa.UniqueConstraint("user_id", "api_key", name="user_api_key_unique"),
    )

    id = sa.Column("id", sa.Integer, autoincrement=True, primary_key=True)
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    api_type = sa.Column("api_type", sa.String, index=True)
    api_key = sa.Column("api_key", sa.String, unique=False, index=True)
    is_active = sa.Column("is_active", sa.Boolean, default=True)
    idem_id = sa.Column("idem_id", sa.String, nullable=False, unique=True)


async def create_tables(aiodb: AsyncDatabase):
    # tables = TableBase.metadata.tables.keys()

    async with aiodb.begin() as conn:
        await conn.run_sync(TableBase.metadata.create_all)
