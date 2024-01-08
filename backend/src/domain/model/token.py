import datetime

from src.domain.model.base import ValueObject


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
