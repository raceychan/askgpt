from askgpt.adapters.factory import adapter_locator
from askgpt.app.auth.service import TokenRegistry
from askgpt.domain.config import SETTINGS_CONTEXT
from askgpt.infra.eventrecord import EventRecord
from askgpt.infra.eventstore import EventStore
from askgpt.infra.security import Encrypt


def event_record_factory():
    return EventRecord(
        consumer=adapter_locator.consumer,
        eventstore=EventStore(aiodb=adapter_locator.aiodb),
        wait_gap=adapter_locator.settings.event_record.EVENT_FETCH_INTERVAL,
    )


def token_registry_factory():
    token_registry = TokenRegistry(
        token_cache=adapter_locator.aiocache,
        keyspace=adapter_locator.aiocache.keyspace.add_cls(TokenRegistry),
    )
    return token_registry


def encrypt_facotry():
    settings = SETTINGS_CONTEXT.get()
    encrypt = Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )
    return encrypt
