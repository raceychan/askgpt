import typing as ty
from functools import lru_cache

import bcrypt
from cryptography.fernet import Fernet
from jose import jwt

from src.domain.model.token import JWTBase

SALT = bcrypt.gensalt()


def hash_password(password: bytes) -> bytes:
    return bcrypt.hashpw(password, SALT)


def verify_password(password: bytes, hashed: bytes) -> bool:
    return bcrypt.checkpw(password, hashed)


def encode_jwt(payload: dict[str, ty.Any], secret_key: str, algorithm: str):
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def decode_jwt(token: str, secret_key: str, algorithm: str) -> dict[str, ty.Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])


@lru_cache(maxsize=1)
def get_fernet(key: bytes):
    return Fernet(key)


def encrypt_string(string: str, key: bytes) -> bytes:
    encryptor = get_fernet(key)
    return encryptor.encrypt(string.encode())


def decrypt_string(string: bytes, key: bytes) -> str:
    fernet = get_fernet(key)
    return fernet.decrypt(string).decode()


class Encrypt:
    def __init__(self, secret_key: str, algorithm: str):
        self._secret_key = secret_key
        self._algorithm = algorithm

    def encrypt_jwt(self, token: JWTBase) -> str:
        return encode_jwt(
            token.asdict(exclude_none=True),
            secret_key=self._secret_key,
            algorithm=self._algorithm,
        )

    def decrypt_jwt(self, encoded_token: str) -> dict[str, str]:
        return decode_jwt(
            encoded_token, secret_key=self._secret_key, algorithm=self._algorithm
        )

    def encrypt_string(self, string: str) -> bytes:
        return encrypt_string(string, self._secret_key.encode())

    def decrypt_string(self, string: bytes) -> str:
        return decrypt_string(string, self._secret_key.encode())
