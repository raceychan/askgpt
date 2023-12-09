import typing as ty

import bcrypt
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


class TokenEncrypt:
    def __init__(self, secret_key: str, algorithm: str):
        self._secret_key = secret_key
        self._algorithm = algorithm

    def encrypt(self, token: JWTBase) -> str:
        return encode_jwt(
            token.asdict(exclude_none=True),
            secret_key=self._secret_key,
            algorithm=self._algorithm,
        )

    def decrypt(self, encoded_token: str) -> dict[str, str]:
        return decode_jwt(
            encoded_token, secret_key=self._secret_key, algorithm=self._algorithm
        )
