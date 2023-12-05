import datetime

import pytest
from sqlalchemy.ext import asyncio as sa_aio

from src.app.auth.repository import UserAuth
from src.app.bootstrap import bootstrap
from src.app.model import TestDefaults
from src.domain.interface import ISettings
from src.infra.cache import LocalCache
from src.infra.eventstore import EventStore


@pytest.fixture(scope="module")
def async_engine(settings: ISettings):
    engine = sa_aio.create_async_engine(
        settings.db.ASYNC_DB_URL,
        echo=settings.db.ENGINE_ECHO,
        pool_pre_ping=True,
        isolation_level=settings.db.ISOLATION_LEVEL,
    )
    return engine


@pytest.fixture(scope="module")
def local_cache():
    return LocalCache.from_singleton()


@pytest.fixture(scope="module", autouse=True)
async def tables(async_engine: sa_aio.AsyncEngine):
    await bootstrap(async_engine)


@pytest.fixture(scope="module")
async def eventstore(async_engine: sa_aio.AsyncEngine) -> EventStore:
    es = EventStore(async_engine)
    return es


@pytest.fixture(scope="module")
def user_auth(test_defaults: TestDefaults):
    return UserAuth(
        user_info=test_defaults.USER_INFO, last_login=datetime.datetime.utcnow()
    )
