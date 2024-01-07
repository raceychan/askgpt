from src.app.api.throttler import UserRequestThrottler
from src.app.auth.repository import UserRepository
from src.app.auth.service import AuthService, TokenRegistry
from src.app.eventrecord import EventRecord
from src.app.gpt.repository import SessionRepository
from src.app.gpt.service import GPTService, GPTSystem, QueueBox
from src.domain.config import Settings, settingfactory
from src.infra import factory as infra_factory
from src.infra.service_registry import Dependency, ServiceRegistryBase


@settingfactory
def get_user_repo(settings: Settings):
    aioengine = infra_factory.get_async_engine(settings)
    user_repo = UserRepository(aioengine)
    return user_repo


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
        keyspace=settings.redis.keyspaces.APP.generate_for_cls(TokenRegistry),
    )


@settingfactory
def get_auth_service(settings: Settings):
    user_repo = get_user_repo(settings)
    token_registry = get_token_registry(settings)
    token_encrypt = infra_factory.get_encrypt(settings)
    producer = infra_factory.get_producer(settings)
    return AuthService(
        user_repo=user_repo,
        token_registry=token_registry,
        token_encrypt=token_encrypt,
        producer=producer,
        security_settings=settings.security,
    )


@settingfactory
def get_gpt_service(settings: Settings):
    aioengine = infra_factory.get_async_engine(settings)
    system = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        boxfactory=QueueBox,
        cache=infra_factory.get_cache(settings),
    )
    session_repo = SessionRepository(aioengine)
    service = GPTService(system=system, session_repo=session_repo)
    return service


def get_user_request_throttler(settings: Settings):
    keyspace = settings.redis.keyspaces.THROTTLER / "global_request"
    bucket_facotry = infra_factory.get_tokenbucket_factory(settings, keyspace)
    throttler = UserRequestThrottler(
        bucket_factory=bucket_facotry,
        max_requests=settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE * 60,
    )
    return throttler


class ApplicationServices(ServiceRegistryBase):
    auth_service = Dependency(AuthService, get_auth_service)
    gpt_service = Dependency(GPTService, get_gpt_service)
    eventrecord = Dependency(EventRecord, get_eventrecord)
