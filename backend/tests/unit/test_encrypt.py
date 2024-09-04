import pytest
from src.domain.model.test_default import TestDefaults
from src.domain.model.user import UserCredential
from src.infra import security

password = TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: UserCredential) -> bytes:
    return security.hash_password(TestDefaults.USER_PASSWORD.encode())


def test_verify_password(hashed: bytes):
    assert security.verify_password(password.encode(), hashed)
