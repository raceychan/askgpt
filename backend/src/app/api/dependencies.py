from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError
from pydantic import ValidationError
from src.app.auth.errors import InvalidCredentialError
from src.app.auth.model import AccessToken
from src.domain.config import get_setting
from src.infra import factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def parse_access_token(token: str = Depends(oauth2_scheme)) -> AccessToken:
    token_encrypt = factory.get_encrypt(get_setting())
    try:
        decoded = token_encrypt.decrypt_jwt(token)
        access_token = AccessToken.model_validate(decoded)
    except (JWTError, ValidationError):
        raise InvalidCredentialError
    return access_token


def throttle_user_usage(
    token: AccessToken = Depends(parse_access_token),
):
    bucket_factory = factory.get_bucket_factory(get_setting())

    bucket_key = f"askgpt:throttler:global_request:{token.sub}"
    bucket = bucket_factory.create_bucket(
        bucket_key=bucket_key, max_tokens=10, refill_rate=0
    )
    return bucket
