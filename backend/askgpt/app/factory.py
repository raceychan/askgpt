from askgpt.helpers.sql import UnitOfWork
from askgpt.api.throttler import UserRequestThrottler
from askgpt.app.auth._repository import AuthRepository
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.app.gpt._repository import SessionRepository
from askgpt.app.gpt.service import AnthropicGPT, OpenAIGPT, SessionService
from askgpt.app.user._repository import UserRepository
from askgpt.app.user.service import UserService
from askgpt.domain.config import SETTINGS_CONTEXT, Settings
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers.functions import simplecache
from askgpt.infra.eventstore import EventStore
from askgpt.infra.factory import encrypt_facotry
from askgpt.infra.locator import adapter_locator


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


def session_service_factory():
    return SessionService(
        session_repo=SessionRepository(uow_factory()), event_store=event_store_factory()
    )


def dynamic_gpt_service_factory(gpt_type: SupportedGPTs):
    auth_service = auth_service_factory()
    event_store = event_store_factory()
    cache = adapter_locator.aiocache
    session_service = session_service_factory()

    if gpt_type == "openai":
        return OpenAIGPT(
            auth_service=auth_service,
            session_service=session_service,
            event_store=event_store,
            cache=cache,
        )
    elif gpt_type == "anthropic":
        return AnthropicGPT(
            auth_service=auth_service,
            session_service=session_service,
            event_store=event_store,
            cache=cache,
        )
    else:
        raise ValueError(f"Unsupported GPT type: {gpt_type}")
