import typing as ty

import bcrypt
from jose import jwt

SALT = bcrypt.gensalt()


def hash_password(password: bytes) -> bytes:
    return bcrypt.hashpw(password, SALT)


def verify_password(password: bytes, hashed: bytes) -> bool:
    return bcrypt.checkpw(password, hashed)


def create_jwt(content: dict[str, ty.Any], secret_key: str, algorithm: str):
    token = jwt.encode(content, secret_key, algorithm=algorithm)
    return token


def decode_jwt(token: str, secret_key: str, algorithm: str) -> dict[str, ty.Any]:
    return jwt.decode(token, secret_key, algorithms=[algorithm])
