import pytest

from src.app import model
from src.domain import encrypt

password = model.TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: model.UserInfo) -> bytes:
    return encrypt.hash_password(model.TestDefaults.USER_PASSWORD.encode())


def test_verify_password(hashed: bytes):
    assert encrypt.verify_password(password.encode(), hashed)
