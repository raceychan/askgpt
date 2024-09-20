import typing as ty
from functools import lru_cache

import bcrypt
from cryptography.fernet import Fernet
from jose import jwt
from jose.exceptions import JWTError as JWTError
from pydantic import ValidationError as ValidationError

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


def decrypt_string(string: bytes, security_key: bytes) -> str:
    fernet = get_fernet(security_key)
    return fernet.decrypt(string).decode()


def generate_secrete() -> bytes:
    return Fernet.generate_key()


if __name__ == "__main__":
    urlsafe_b64encode = generate_secrete()
    print(f"{urlsafe_b64encode=}")
