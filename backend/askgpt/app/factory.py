from askgpt.adapters.factory import adapter_locator
from askgpt.app.api.throttler import UserRequestThrottler
from askgpt.app.auth.service import AuthService
from askgpt.app.gpt.service import GPTService, GPTSystem, QueueBox
from askgpt.domain.config import Settings
from askgpt.infra import factory as infra_factory


def user_request_throttler_factory():
    keyspace = adapter_locator.settings.redis.keyspaces.THROTTLER / "user_request"
    throttler = UserRequestThrottler(
        bucket_factory=adapter_locator.build_token_bucket(keyspace=keyspace),
        max_requests=adapter_locator.settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=adapter_locator.settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE
        * 60,
    )
    return throttler


def auth_service_factory(settings: Settings | None = None):
    settings = adapter_locator.settings
    auth_service = AuthService(
        user_repo=infra_factory.user_repo_factory(),
        token_registry=infra_factory.token_registry_factory(),
        token_encrypt=infra_factory.encrypt_facotry(),
        producer=infra_factory.producer_factory(),
        security_settings=settings.security,
    )
    return auth_service


def gpt_service_factory(settings: Settings | None = None):
    settings = settings or adapter_locator.settings
    system = GPTSystem(
        settings=settings,
        ref=settings.actor_refs.SYSTEM,
        boxfactory=QueueBox,
        cache=infra_factory.cache_factory(),
    )

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


# class service_locator(ServiceLocator[ty.Any]):
#     "singleton class for service locator"

#     # auth_service: Dependency[AuthService] = auth_servie_factory
#     auth_service = Dependency(AuthService, auth_service_factory)
#     gpt_service = Dependency(GPTService, gpt_service_factory)