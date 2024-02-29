import typing as ty

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError
from pydantic import ValidationError
from src.adapters.factory import adapter_locator
from src.app import factory as app_fatory
from src.app.api.errors import QuotaExceededError
from src.app.auth.errors import InvalidCredentialError
from src.app.auth.model import AccessToken
from src.infra import factory as infra_factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def parse_access_token(token: str = Depends(oauth2_scheme)) -> AccessToken:
    token_encrypt = infra_factory.encrypt_facotry()
    try:
        decoded = token_encrypt.decrypt_jwt(token)
        access_token = AccessToken.model_validate(decoded)
    except (JWTError, ValidationError) as e:
        raise InvalidCredentialError from e
    return access_token


async def throttle_user_request(
    access_token: ty.Annotated[AccessToken, Depends(parse_access_token)],
):
    throttler = app_fatory.user_request_throttler_factory()
    wait_time = await throttler.validate(access_token.sub)
    if wait_time:
        raise QuotaExceededError(throttler.max_tokens, wait_time)
