from askgpt.app.api.throttler import UserRequestThrottler
from askgpt.app.auth.repository import UserRepository
from askgpt.app.auth.service import AuthService, TokenRegistry
from askgpt.app.gpt.repository import SessionRepository
from askgpt.app.gpt.service import GPTService, GPTSystem, QueueBox
from askgpt.domain.config import SETTINGS_CONTEXT, Settings
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
        keyspace=adapter_locator.aiocache.keyspace.add_cls(TokenRegistry),
    )
    return token_registry


def auth_service_factory():
    settings: Settings = SETTINGS_CONTEXT.get()
    auth_service = AuthService(
        user_repo=UserRepository(adapter_locator.aiodb),
        token_registry=token_registry_factory(),
        token_encrypt=encrypt_facotry(),
        producer=adapter_locator.producer,
        security_settings=settings.security,
    )
    return auth_service


def gpt_service_factory():
    settings: Settings = SETTINGS_CONTEXT.get()
    system = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        boxfactory=QueueBox,
        cache=adapter_locator.aiocache,
    )

    session_repo = SessionRepository(adapter_locator.aiodb)
    user_repo = UserRepository(adapter_locator.aiodb)
    encryptor = encrypt_facotry()
    producer = adapter_locator.producer
    service = GPTService(
        system=system,
        encryptor=encryptor,
        user_repo=user_repo,
        session_repo=session_repo,
        producer=producer,
    )
    return service
