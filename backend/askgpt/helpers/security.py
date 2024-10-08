import hashlib
import hmac
import typing as ty
from functools import lru_cache

import bcrypt
from cryptography.fernet import Fernet
from jose.exceptions import JWTError as JWTError
from jose.jwt import decode as jwt_decode
from jose.jwt import encode as jwt_encode
from pydantic import ValidationError as ValidationError


def gensalt(round: int = 12, prefix: bytes = b"2b") -> bytes:
    """
    Genearte a random bytes used in hashing
    """
    return bcrypt.gensalt(round, prefix)


def hash_password(password: bytes) -> bytes:
    return bcrypt.hashpw(password, gensalt())


def verify_password(password: bytes, hashed: bytes) -> bool:
    return bcrypt.checkpw(password, hashed)


def encode_jwt(payload: dict[str, ty.Any], secret_key: str, algorithm: str):
    token = jwt_encode(payload, secret_key, algorithm=algorithm)

    return token


def decode_jwt(token: str, secret_key: str, algorithm: str) -> dict[str, ty.Any]:
    return jwt_decode(token, secret_key, algorithms=[algorithm])


def hash_256(secret_string: str, secrete_key: str) -> bytes:
    hashed = hmac.new(
        secrete_key.encode(), secret_string.encode(), hashlib.sha256
    ).digest()
    return hashed


# The Fernet Algorithm


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
