import pytest
from askgpt.app.auth.model import UserCredential
from askgpt.infra import security
from tests.conftest import TestDefaults

password = TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: UserCredential) -> bytes:
    return security.hash_password(TestDefaults.USER_PASSWORD.encode())


def test_verify_password(hashed: bytes):
    assert security.verify_password(password.encode(), hashed)
