import pytest

from src.app.gpt import model
from src.domain import encrypt

password = model.TestDefaults.USER_PASSWORD


@pytest.fixture(scope="module")
def hashed(user_info: model.UserInfo):
    return encrypt.hash_password(model.TestDefaults.USER_PASSWORD)


def test_verify_password(hashed: bytes):
    assert encrypt.verify_password(password, hashed)


def test_multiple_hashes_are_different():
    hashed = encrypt.hash_password(password)
    for _ in range(2):
        hashed = encrypt.hash_password(password)
    assert encrypt.verify_password(password, hashed)
