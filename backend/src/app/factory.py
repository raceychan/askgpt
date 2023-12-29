from src.app.auth.repository import UserRepository
from src.app.auth.service import AuthService, TokenRegistry
from src.app.eventrecord import EventRecord
from src.domain.config import Settings, settingfactory
from src.infra import factory as infra_factory


@settingfactory
def get_eventrecord(settings: Settings):
    return EventRecord(
        consumer=infra_factory.get_consumer(settings),
        eventstore=infra_factory.get_eventstore(settings),
        wait_gap=settings.event_record.EventFetchInterval,
    )


@settingfactory
def get_token_registry(settings: Settings):
    return TokenRegistry(
        token_cache=infra_factory.get_cache(settings),
        keyspace=settings.redis.KEY_SPACE("token_registry"),
    )


@settingfactory
def get_user_repo(settings: Settings):
    aioengine = infra_factory.get_async_engine(settings)
    user_repo = UserRepository(aioengine)
    return user_repo


@settingfactory
def get_auth_service(settings: Settings):
    user_repo = get_user_repo(settings)
    token_registry = get_token_registry(settings)
    token_encrypt = infra_factory.get_encrypt(settings)
    producer = infra_factory.get_producer(settings)
    security_settings = settings.security
    return AuthService(
        user_repo=user_repo,
        token_registry=token_registry,
        token_encrypt=token_encrypt,
        producer=producer,
        security_settings=security_settings,
    )
