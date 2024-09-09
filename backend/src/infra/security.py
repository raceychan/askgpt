import datetime
import typing as ty
from functools import lru_cache

import bcrypt
from cryptography.fernet import Fernet
from jose import jwt
from jose.exceptions import JWTError as JWTError
from pydantic import ValidationError as ValidationError
from src.domain.model.base import ValueObject

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




class JWTBase(ValueObject):
    # reff: https://en.wikipedia.org/wiki/JSON_Web_Token
    """
    | Code | Name | Description |
    | ---- | ---- | ----------- |
    | iss  | Issuer |	principal that issued the JWT.|
    | sub  | Subject | the subject of the JWT.|
    | aud  | Audience |  the recipients that the JWT is intended for. |
    | exp | Expiration Time |	the expiration time on and after which the JWT must not be accepted for processing.|
    | nbf |	Not Before | the time on which the JWT will start to be accepted for processing. The value must be a NumericDate.|
    | iat | Issued at |	 the time at which the JWT was issued. The value must be a NumericDate.|
    | jti | JWT ID | Case-sensitive unique identifier of the token even among different issuers.|
    """
    sub: str
    exp: datetime.datetime
    nbf: datetime.datetime
    iat: datetime.datetime
    iss: str | None = None
    aud: str | None = None
    jti: str | None = None

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

    def decrypt_string(self, encrypted: bytes) -> str:
        return decrypt_string(encrypted, self._secret_key.encode())
