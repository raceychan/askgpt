from datetime import datetime

from src.app import factory
from src.app.auth import model, repository
from src.app.error import ClientSideError
from src.domain import encrypt
from src.domain._log import logger
from src.domain.config import Settings
from src.domain.interface import IEvent
from src.domain.model import uuid_factory
from src.infra.cache import Cache, LocalCache
from src.infra.mq import MessageProducer


class Authenticator:
    """
    On every user request for content that might need authentication,
    ensure that token is in the user's Redis store i.e ${userId}-tokens.
    If the token is not in the Redis store, then it is not a valid token anymore.
    """

    def __init__(
        self,
        token_cache: Cache[str, str],
        secrete_key: str,
        encode_algo: str,
        ttl_m: int,
    ):
        self._token_cache = token_cache
        self._secrete_key = secrete_key
        self._encode_algo = encode_algo
        self._ttl_m = ttl_m

    async def is_authenticated(self, access_token: str) -> bool:
        token = encrypt.decode_jwt(
            access_token, secret_key=self._secrete_key, algorithm=self._encode_algo
        )
        cached_token = await self._token_cache.get(token["user_id"])
        return bool(cached_token)

    async def authenticate(self, user_auth: model.UserAuth) -> str:
        token = self.create_access_token(user_auth.entity_id, user_auth.role)
        await self._token_cache.set(user_auth.entity_id, token)
        return token

    def create_jwt(self, content: dict[str, str]):
        return encrypt.create_jwt(
            content, secret_key=self._secrete_key, algorithm=self._encode_algo
        )

    def create_access_token(self, user_id: str, user_role: model.UserRoles) -> str:
        token = model.AccessToken(ttl_m=self._ttl_m, user_id=user_id, role=user_role)
        encoded_jwt = self.create_jwt(token.asdict())
        return encoded_jwt

    async def revoke_token(self, user_id: str, token: str) -> None:
        """
        revoke token from user
        """
        await self._token_cache.remove(user_id)

    @classmethod
    def build(cls, settings: Settings) -> "Authenticator":
        cache = LocalCache[str, str].from_singleton()
        return cls(
            token_cache=cache,
            secrete_key=settings.security.SECRET_KEY,
            encode_algo=settings.security.ALGORITHM,
            ttl_m=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES,
        )


class AuthenticationError(ClientSideError):
    service: str = "auth"


class UserNotFoundError(AuthenticationError):
    """
    Unable to find user with the same email
    """


class InvalidPasswordError(AuthenticationError):
    """
    User email and password does not match
    """


class UserAlreadyExistError(AuthenticationError):
    """
    User with the same email already exist
    """


class AuthService:
    def __init__(
        self,
        user_repo: repository.UserRepository,
        authenticator: Authenticator,
        producer: MessageProducer[IEvent],
    ):
        self._user_repo = user_repo
        self._auth = authenticator
        self._producer = producer

    @property
    def user_repo(self):
        return self._user_repo

    async def login(self, email: str, password: str) -> str:
        user = await self._user_repo.search_user_by_email(email)

        if user is None:
            raise UserNotFoundError("user not found")

        if not user.user_info.verify_password(password):
            raise InvalidPasswordError("Invalid password")

        user.login()

        logger.success(f"User {user.entity_id} logged in")
        return await self._auth.authenticate(user)

    async def is_user_authenticated(self, access_token: str) -> bool:
        return await self._auth.is_authenticated(access_token=access_token)

    async def find_user(self, useremail: str) -> model.UserAuth | None:
        """
        make sure user does not exist
        """
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    async def signup_user(self, user_name: str, email: str, password: str) -> str:
        user = await self.find_user(email)
        if user is not None:
            raise UserAlreadyExistError(f"user {email} already exist")

        hash_password = encrypt.hash_password(password.encode())
        user_info = model.UserInfo(
            user_name=user_name, user_email=email, hash_password=hash_password
        )
        user_signed_up = model.UserSignedUp(
            user_id=uuid_factory(),
            user_info=user_info,
            last_login=datetime.utcnow(),
        )
        user_auth = model.UserAuth.apply(user_signed_up)
        await self._user_repo.add(user_auth)
        await self._producer.publish(user_signed_up)
        return user_auth.entity_id

    @classmethod
    def build(cls, settings: Settings) -> "AuthService":
        aioengine = factory.get_async_engine(settings)
        user_repo = repository.UserRepository(aioengine)
        return cls(
            user_repo=user_repo,
            authenticator=Authenticator.build(settings=settings),
            producer=factory.get_producer(settings=settings),
        )
