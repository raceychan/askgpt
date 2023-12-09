from functools import lru_cache

#
from src.app.auth.service import Authenticator
from src.app.eventrecord import EventRecord
from src.domain.config import Settings
from src.infra.factory import (
    get_consumer,
    get_eventstore,
    get_localcache,
    get_token_encrypt,
)


@lru_cache(maxsize=1)
def get_eventrecord(settings: Settings):
    return EventRecord(
        consumer=get_consumer(settings),
        eventstore=get_eventstore(settings),
    )


@lru_cache(maxsize=1)
async def get_authenticator(settings: Settings):
    return Authenticator(
        token_cache=get_localcache(),
        token_encrypt=get_token_encrypt(settings=settings),
        token_ttl=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


# def get_auth_service(settings: Settings):
#     return Authenticator(
#         token_cache=LocalCache(),
#         secrete_key=settings.auth.SECRET_KEY,
#         encode_algo=settings.auth.ENCODE_ALGO,
#         ttl_m=settings.auth.TTL_M,
#     )
