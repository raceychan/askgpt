import pytest

from src.app.gpt import model
from src.domain import encrypt

password = model.TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: model.UserInfo) -> bytes:
    return encrypt.hash_password(model.TestDefaults.USER_PASSWORD.encode())


def test_verify_password(hashed: bytes):
    assert encrypt.verify_password(password.encode(), hashed)


def test_multiple_hashes_are_different():
    hashed = encrypt.hash_password(password.encode())
    for _ in range(2):
        hashed = encrypt.hash_password(password.encode())
    assert encrypt.verify_password(password.encode(), hashed)
