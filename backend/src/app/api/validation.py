from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError
from pydantic import ValidationError

from src.app.auth.errors import InvalidCredentialError
from src.app.auth.model import AccessToken
from src.domain.config import get_setting
from src.infra import factory

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
token_encrypt = factory.get_encrypt(get_setting())


def parse_access_token(token: str = Depends(oauth2_scheme)) -> AccessToken:
    try:
        decoded = token_encrypt.decrypt_jwt(token)
        access_token = AccessToken.model_validate(decoded)
    except (JWTError, ValidationError):
        raise InvalidCredentialError
    return access_token
