from askgpt.api.throttler import UserRequestThrottler
from askgpt.app.auth.repository import AuthRepository
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.app.gpt.repository import SessionRepository
from askgpt.app.gpt.service import GPTService, GPTSystem, QueueBox
from askgpt.app.user.repository import UserRepository
from askgpt.app.user.service import UserService
from askgpt.domain.config import SETTINGS_CONTEXT, Settings
from askgpt.helpers.functions import simplecache
from askgpt.infra.eventstore import EventStore, OutBoxProducer
from askgpt.infra.factory import encrypt_facotry
from askgpt.infra.locator import adapter_locator
from askgpt.infra.uow import UnitOfWork


def user_request_throttler_factory():
    settings: Settings = SETTINGS_CONTEXT.get()
    keyspace = settings.redis.keyspaces.THROTTLER / "user_request"
    throttler = UserRequestThrottler(
        bucket_factory=adapter_locator.build_token_bucket(keyspace=keyspace),
        max_requests=settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE * 60,
    )
    return throttler


def token_registry_factory():
    token_registry = TokenRegistry(
        token_cache=adapter_locator.aiocache,
        keyspace=adapter_locator.aiocache.keyspace.cls_keyspace(TokenRegistry),
    )
    return token_registry


@simplecache
def event_store_factory():
    return EventStore(uow=uow_factory())


@simplecache
def outbox_producer_factory():
    return OutBoxProducer(eventstore=event_store_factory())


@simplecache
def uow_factory() -> UnitOfWork:
    uow = UnitOfWork(adapter_locator.aiodb)
    return uow


def user_service_factory():
    return UserService(
        user_repo=UserRepository(uow_factory()),
        event_store=event_store_factory(),
    )


def auth_service_factory():
    settings: Settings = SETTINGS_CONTEXT.get()
    auth_service = AuthService(
        auth_repo=AuthRepository(uow_factory()),
        token_registry=token_registry_factory(),
        encryptor=encrypt_facotry(),
        eventstore=event_store_factory(),
        security_settings=settings.security,
    )
    return auth_service


def gpt_service_factory():
    settings: Settings = SETTINGS_CONTEXT.get()
    system: GPTSystem = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        event_store=event_store_factory(),
        boxfactory=QueueBox,
        cache=adapter_locator.aiocache,
        producer=outbox_producer_factory(),
    )

    session_repo = SessionRepository(uow_factory())
    user_repo = AuthRepository(uow_factory())
    encryptor = encrypt_facotry()
    producer = outbox_producer_factory()
    service = GPTService(
        system=system,
        encryptor=encryptor,
        user_repo=user_repo,
        session_repo=session_repo,
        producer=producer,
    )
    return service
