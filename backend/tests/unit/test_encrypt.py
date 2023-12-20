import pytest

from src.domain.model.test_default import TestDefaults
from src.domain.model.user import UserInfo
from src.infra import encrypt

password = TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: UserInfo) -> bytes:
    return encrypt.hash_password(TestDefaults.USER_PASSWORD.encode())


def test_verify_password(hashed: bytes):
    assert encrypt.verify_password(password.encode(), hashed)
