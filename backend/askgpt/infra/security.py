import datetime

from jose.exceptions import JWTError as JWTError
from pydantic import ValidationError as ValidationError

from askgpt.domain.model.base import ValueObject
from askgpt.helpers.security import (
    hash_password as hash_password,
    verify_password as verify_password,
    decode_jwt as decode_jwt,
    decrypt_string as decrypt_string,
    encode_jwt as encode_jwt,
    encrypt_string as encrypt_string,
)


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
