from askgpt.adapters import factory as adapter_factory
from askgpt.app.auth.repository import UserRepository
from askgpt.app.auth.service import TokenRegistry
from askgpt.app.gpt.repository import SessionRepository
from askgpt.infra import security
from askgpt.infra.eventrecord import EventRecord
from askgpt.infra.eventstore import EventStore


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
        token_cache=adapter_factory.adapter_locator.aiocache,
        keyspace=adapter_factory.adapter_locator.aiocache.keyspace.add_cls(
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
    return adapter_factory.adapter_locator.aiocache
