from src.adapters import factory as adapter_factory
from src.app.api.throttler import UserRequestThrottler
from src.app.auth.service import AuthService
from src.app.gpt.repository import SessionRepository
from src.app.gpt.service import GPTService, GPTSystem, QueueBox
from src.domain.config import Settings, settingfactory
from src.infra import factory as infra_factory


@settingfactory
def get_auth_service(settings: Settings):
    user_repo = infra_factory.get_user_repo(settings)
    token_registry = infra_factory.get_token_registry(settings)
    token_encrypt = infra_factory.get_encrypt(settings)
    producer = adapter_factory.get_producer(settings)
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
        cache=adapter_factory.get_cache(settings),
    )
    session_repo = infra_factory.get_session_repo(settings)
    service = GPTService(system=system, session_repo=session_repo)
    return service


@settingfactory
def get_user_request_throttler(settings: Settings):
    keyspace = settings.redis.keyspaces.THROTTLER / "user_request"
    bucket_facotry = adapter_factory.get_tokenbucket_factory(settings, keyspace)
    throttler = UserRequestThrottler(
        bucket_factory=bucket_facotry,
        max_requests=settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE * 60,
    )
    return throttler
