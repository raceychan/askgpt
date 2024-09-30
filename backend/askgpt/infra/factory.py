from askgpt.domain.config import SETTINGS_CONTEXT
from askgpt.infra.eventrecord import EventListener
from askgpt.infra.eventstore import EventStore
from askgpt.infra.locator import adapter_locator
from askgpt.infra.security import Encrypt


def event_listener_factory():
    return EventListener(
        consumer=adapter_locator.consumer,
        eventstore=EventStore(aiodb=adapter_locator.aiodb),
        wait_gap=adapter_locator.settings.event_record.EVENT_FETCH_INTERVAL,
    )


def encrypt_facotry():
    settings = SETTINGS_CONTEXT.get()
    encrypt = Encrypt(
        secret_key=settings.security.SECRET_KEY,
        algorithm=settings.security.ALGORITHM,
    )
    return encrypt
