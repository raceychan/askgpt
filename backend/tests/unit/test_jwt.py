import datetime

import pytest
from tests.conftest import UserDefaults

from askgpt.app.auth.model import AccessToken
from askgpt.domain.config import SecretStr, Settings
from askgpt.domain.model.base import utc_now
from askgpt.infra import security


@pytest.fixture(scope="module")
def token_encrypt(settings: Settings) -> security.Encryptor:
    return security.Encryptor(
        secret_key=settings.security.SECRET_KEY.get_secret_value(),
        algorithm=settings.security.ALGORITHM,
    )


def test_encryp_access_token(
    test_defaults: UserDefaults, token_encrypt: security.Encryptor, settings: Settings
):
    now_ = utc_now()
    token = AccessToken(
        sub=test_defaults.USER_ID,
        role=test_defaults.USER_ROLE,
        exp=now_
        + datetime.timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES),
        nbf=now_,
        iat=now_,
    )
    encoded = token_encrypt.encrypt_jwt(token)

    data = token_encrypt.decrypt_jwt(encoded)
    decoded = AccessToken.model_validate(data)
    assert decoded.sub == test_defaults.USER_ID
    assert decoded.role == test_defaults.USER_ROLE
