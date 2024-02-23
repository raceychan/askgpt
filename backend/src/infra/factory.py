from src.adapters import factory as adapter_factory
from src.app.auth.repository import UserRepository
from src.app.auth.service import TokenRegistry
from src.app.gpt.repository import SessionRepository
from src.domain.config import Settings, settingfactory
from src.infra import security
from src.infra.eventrecord import EventRecord


def make_encrypt(settings: Settings) -> security.Encrypt:
    return security.Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )


@settingfactory
def make_user_repo(settings: Settings):
    database = adapter_factory.make_database(settings)
    user_repo = UserRepository(database)
    return user_repo


@settingfactory
def make_session_repo(settings: Settings):
    database = adapter_factory.make_database(settings)
    session_repo = SessionRepository(database)
    return session_repo


@settingfactory
def make_eventrecord(settings: Settings):
    return EventRecord(
        consumer=adapter_factory.make_consumer(settings),
        eventstore=adapter_factory.make_eventstore(settings),
        wait_gap=settings.event_record.EVENT_FETCH_INTERVAL,
    )


@settingfactory
def make_token_registry(settings: Settings):
    return TokenRegistry(
        token_cache=adapter_factory.make_cache(settings),
        keyspace=settings.redis.keyspaces.APP.generate_for_cls(TokenRegistry),
    )


# ===== Experimental =====
def user_repo_factory():
    aiodb = adapter_factory.AdapterLocator.aiodb
    user_repo = UserRepository(aiodb)
    return user_repo


def session_repo_factory():
    aiodb = adapter_factory.AdapterLocator.aiodb
    session_repo = SessionRepository(aiodb)
    return session_repo


def token_registry_factory():
    token_registry = TokenRegistry(
        token_cache=adapter_factory.AdapterLocator.redis_cache,
        keyspace=adapter_factory.AdapterLocator.redis_cache.keyspace.generate_for_cls(
            TokenRegistry
        ),
    )
    return token_registry


def encrypt_facotry():
    encrypt = security.Encrypt(
        secret_key=adapter_factory.AdapterLocator.settings.security.SECRET_KEY,
        algorithm=adapter_factory.AdapterLocator.settings.security.ALGORITHM,
    )
    return encrypt


def producer_factory():
    return adapter_factory.AdapterLocator.producer


def cache_factory():
    return adapter_factory.AdapterLocator.redis_cache
