from src.adapters import factory as adapter_factory
from src.app.auth.repository import UserRepository
from src.app.auth.service import TokenRegistry
from src.app.gpt.repository import SessionRepository
from src.infra import security
from src.infra.eventrecord import EventRecord
from src.infra.eventstore import EventStore


def event_record_factory():
    locator = adapter_factory.adapter_locator

    return EventRecord(
        consumer=locator.consumer,
        eventstore=EventStore(aiodb=locator.aiodb),
        wait_gap=locator.settings.event_record.EVENT_FETCH_INTERVAL,
    )


def user_repo_factory():
    aiodb = adapter_factory.adapter_locator.aiodb
    user_repo = UserRepository(aiodb)
    return user_repo


def session_repo_factory():
    aiodb = adapter_factory.adapter_locator.aiodb
    session_repo = SessionRepository(aiodb)
    return session_repo


def token_registry_factory():
    token_registry = TokenRegistry(
        token_cache=adapter_factory.adapter_locator.redis_cache,
        keyspace=adapter_factory.adapter_locator.redis_cache.keyspace.add_cls(
            TokenRegistry
        ),
    )
    return token_registry


def encrypt_facotry():
    encrypt = security.Encrypt(
        secret_key=adapter_factory.adapter_locator.settings.security.SECRET_KEY,
        algorithm=adapter_factory.adapter_locator.settings.security.ALGORITHM,
    )
    return encrypt


def producer_factory():
    return adapter_factory.adapter_locator.producer


def cache_factory():
    return adapter_factory.adapter_locator.redis_cache
