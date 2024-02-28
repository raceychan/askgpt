import typing as ty

from src.adapters import factory as adapter_factory
from src.app.api.throttler import UserRequestThrottler
from src.app.auth.service import AuthService
from src.app.gpt.service import GPTService, GPTSystem, QueueBox
from src.domain.config import Settings, settingfactory
from src.infra import factory as infra_factory
from backend.src.infra.service_locator import Dependency, ServiceLocator


@settingfactory
def get_auth_service(settings: Settings):
    user_repo = infra_factory.make_user_repo(settings)
    token_registry = infra_factory.make_token_registry(settings)
    token_encrypt = infra_factory.make_encrypt(settings)
    producer = adapter_factory.make_producer(settings)
    return AuthService(
        user_repo=user_repo,
        token_registry=token_registry,
        token_encrypt=token_encrypt,
        producer=producer,
        security_settings=settings.security,
    )


@settingfactory
def get_gpt_service(settings: Settings):
    system = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        boxfactory=QueueBox,
        cache=adapter_factory.make_cache(settings),
    )
    user_repo = infra_factory.make_user_repo(settings)
    session_repo = infra_factory.make_session_repo(settings)
    encryptor = infra_factory.make_encrypt(settings)
    producer = adapter_factory.make_producer(settings)
    service = GPTService(
        system=system,
        encryptor=encryptor,
        user_repo=user_repo,
        session_repo=session_repo,
        producer=producer,
    )
    return service


@settingfactory
def get_user_request_throttler(settings: Settings):
    keyspace = settings.redis.keyspaces.THROTTLER / "user_request"
    bucket_facotry = adapter_factory.make_tokenbucket_factory(settings, keyspace)
    throttler = UserRequestThrottler(
        bucket_factory=bucket_facotry,
        max_requests=settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE * 60,
    )
    return throttler


# ==================== Experimental ====================


def auth_service_factory(settings: Settings):
    auth_service = AuthService(
        user_repo=infra_factory.user_repo_factory(),
        token_registry=infra_factory.token_registry_factory(),
        token_encrypt=infra_factory.encrypt_facotry(),
        producer=infra_factory.producer_factory(),
        security_settings=settings.security,
    )
    return auth_service


def gpt_service_factory(settings: Settings):
    system = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        boxfactory=QueueBox,
        cache=infra_factory.cache_factory(),
    )

    # TODO: use lambda instead, session_repo = lambda: SessionRepository(aiodb)
    session_repo = infra_factory.session_repo_factory()
    user_repo = infra_factory.user_repo_factory()
    encryptor = infra_factory.encrypt_facotry()
    producer = infra_factory.producer_factory()
    service = GPTService(
        system=system,
        encryptor=encryptor,
        user_repo=user_repo,
        session_repo=session_repo,
        producer=producer,
    )
    return service


class AppServiceLocator(ServiceLocator[ty.Any]):
    auth_service = Dependency(AuthService, auth_service_factory)
    gpt_service = Dependency(GPTService, gpt_service_factory)
