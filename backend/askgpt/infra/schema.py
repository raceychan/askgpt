import sqlalchemy as sa

from askgpt.adapters.database import AsyncDatabase
from askgpt.helpers.sql import TableBase


class DomainEventsTable(TableBase):
    """
    TODO:
    1. add consumed_at column, sa.Datetime
    """

    __tablename__: str = "domain_events"
    id = sa.Column("id", sa.String, primary_key=True)
    event_type = sa.Column("event_type", sa.String, index=True)
    event_body = sa.Column("event_body", sa.JSON)
    entity_id = sa.Column("entity_id", sa.String, index=True)
    version = sa.Column("version", sa.String, index=True)
    # consumed_at: sa.DateTime, nullable=True


# class EventTaskScheduleTable(DomainEventsTable):
#     __tablename__: str = "event_task_schedule"
#     status = sa.Column("status", sa.String, index=True)  # started, failed
#     retries = sa.Column("retries", sa.Integer, default=0)
#     completed_at = sa.Column("completed_at", sa.DateTime, nullable=True)


class UsersTable(TableBase):
    __tablename__: str = "users"

    id = sa.Column("id", sa.String, primary_key=True)
    username = sa.Column("username", sa.String, unique=False, index=True)
    email = sa.Column("email", sa.String, unique=True, index=True)
    password_hash = sa.Column("password_hash", sa.String, nullable=False)
    last_login = sa.Column("last_login", sa.DateTime, nullable=True)
    role = sa.Column("role", sa.String, nullable=False)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class SessionsTable(TableBase):
    __tablename__: str = "sessions"

    id = sa.Column("id", sa.String, primary_key=True, comment="session_id")
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    session_name = sa.Column("session_name", sa.String, unique=False, index=False)
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class UserAPIKeysTable(TableBase):
    """
    user_key_name_unique: user should not have two api keys with the same name
    user_idem_id_unique: since user api key would be encrypted and same api key would turn into different encrypted value,
    we need to use idem_id to identify the api key
    """

    __tablename__: str = "user_api_keys"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "key_name", name="user_key_name_unique"),
        sa.UniqueConstraint("user_id", "idem_id", name="user_idem_id_unique"),
    )

    id = sa.Column("id", sa.Integer, autoincrement=True, primary_key=True)
    user_id = sa.Column("user_id", sa.String, sa.ForeignKey("users.id"))
    api_type = sa.Column("api_type", sa.String, index=True)
    api_key = sa.Column("api_key", sa.String, unique=False, index=False)
    key_name = sa.Column("key_name", sa.String, unique=False, index=True)
    is_active = sa.Column("is_active", sa.Boolean, default=True)
    idem_id = sa.Column("idem_id", sa.String, nullable=False, unique=False)


async def create_tables(aiodb: AsyncDatabase):
    # tables = TableBase.metadata.tables.keys()

    async with aiodb.begin() as conn:
        await conn.run_sync(TableBase.metadata.create_all)
