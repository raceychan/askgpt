from askgpt.adapters.cache import RedisCache
from askgpt.adapters.tokenbucket import TokenBucketFactory
from askgpt.api.throttler import UserRequestThrottler
from askgpt.app.gpt._repository import SessionRepository
from askgpt.app.gpt.service import AnthropicGPT, OpenAIGPT, SessionService
from askgpt.app.user._repository import UserRepository
from askgpt.app.user.service import UserService
from askgpt.domain.config import Settings, dg
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers.sql import IEngine, UnitOfWork
from askgpt.infra.eventstore import EventStore


@dg.node
def token_bucket_factory(
    settings: Settings, aiocache: RedisCache[str]
) -> TokenBucketFactory:
    keyspace = settings.redis.keyspaces.THROTTLER / "user_request"
    script = settings.redis.TOKEN_BUCKET_SCRIPT
    script_func = aiocache.load_script(script)
    return TokenBucketFactory(
        redis=aiocache,
        script=script_func,
        keyspace=keyspace,
    )


def user_request_throttler_factory(
    settings: Settings, token_bucket_factory: TokenBucketFactory
) -> UserRequestThrottler:
    throttler = UserRequestThrottler(
        bucket_factory=token_bucket_factory,
        max_requests=settings.throttling.USER_MAX_REQUEST_PER_MINUTE,
        refill_duration_s=settings.throttling.USER_MAX_REQUEST_DURATION_MINUTE * 60,
    )
    return throttler


@dg.node
def uow_factory(aiodb: IEngine) -> UnitOfWork:
    uow = UnitOfWork(aiodb)
    return uow


@dg.node
def event_store_factory(uow: UnitOfWork) -> EventStore:
    return EventStore(uow=uow)


def user_service_factory(uow: UnitOfWork) -> UserService:
    return UserService(
        user_repo=UserRepository(uow),
        event_store=event_store_factory(uow),
    )


@dg.node
def session_service_factory(uow: UnitOfWork) -> SessionService:
    return SessionService(
        session_repo=SessionRepository(uow), event_store=event_store_factory(uow)
    )


def session_service_resolver() -> SessionService:
    return dg.resolve(SessionService)


def user_service_resolver() -> UserService:
    return dg.resolve(UserService)


def dynamic_gpt_service_factory(gpt_type: SupportedGPTs):
    if gpt_type == "openai":
        return dg.resolve(OpenAIGPT)
    elif gpt_type == "anthropic":
        return dg.resolve(AnthropicGPT)
    else:
        raise ValueError(f"Unsupported GPT type: {gpt_type}")
