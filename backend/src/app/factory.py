#
from src.app.auth.service import TokenRegistry
from src.app.eventrecord import EventRecord
from src.domain.config import Settings, settingfactory
from src.infra.factory import get_cache, get_consumer, get_eventstore


@settingfactory
def get_eventrecord(settings: Settings):
    return EventRecord(
        consumer=get_consumer(settings),
        eventstore=get_eventstore(settings),
        wait_gap=settings.event_record.EventFetchInterval,
    )


@settingfactory
async def get_token_registry(settings: Settings):
    return TokenRegistry(cache=get_cache(settings))
