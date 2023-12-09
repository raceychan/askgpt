import datetime

import pytest

from src.app.auth.model import AccessToken
from src.domain.config import Settings
from src.domain.model.base import utcts_factory
from src.domain.model.test_default import TestDefaults
from src.infra import encrypt


@pytest.fixture(scope="module")
def token_encrypt(settings: Settings) -> encrypt.TokenEncrypt:
    return encrypt.TokenEncrypt(
        secret_key=settings.security.SECRET_KEY, algorithm=settings.security.ALGORITHM
    )


def test_encryp_access_token(
    test_defaults: TestDefaults, token_encrypt: encrypt.TokenEncrypt, settings: Settings
):
    now_ = utcts_factory()
    token = AccessToken(
        sub=test_defaults.USER_ID,
        role=test_defaults.USER_ROLE,
        exp=now_
        + datetime.timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES),
        nbf=now_,
        iat=now_,
    )
    encoded = token_encrypt.encrypt(token)

    data = token_encrypt.decrypt(encoded)
    decoded = AccessToken.model_validate(data)
    assert decoded.sub == test_defaults.USER_ID
    assert decoded.role == test_defaults.USER_ROLE
