from datetime import datetime, timedelta

from src.app.auth import model, repository
from src.app.error import ClientSideError
from src.domain._log import logger
from src.domain.config import Settings, TimeScale
from src.domain.interface import IEvent
from src.domain.model.base import utcts_factory, uuid_factory
from src.infra import cache, encrypt, factory, mq


class TokenRegistry:
    # infra layer abstraction of cache
    def __init__(self, cache: cache.Cache[str, str]):
        self._cache = cache

    async def register_token(self, user_id: str, token: str) -> None:
        """
        Register token to user
        """

    async def revoke_token(self, user_id: str, token: str) -> None:
        """
        Revoke token from user
        """


class Authenticator:
    # TODO: this should be rewritten as a TokenRegistry
    # which is an infra layer abstraction of cache
    """
    On every user request for content that might need authentication,
    ensure that token is in the user's Redis store i.e ${userId}-tokens.
    If the token is not in the Redis store, then it is not a valid token anymore.
    """

    def __init__(
        self,
        token_cache: cache.Cache[str, str],
        token_encrypt: encrypt.TokenEncrypt,
        token_ttl: TimeScale.Minute,
    ):
        self._token_cache = token_cache
        self._token_encrypt = token_encrypt
        self._ttl_m = token_ttl

    async def is_access_token_valid(self, access_token: str) -> bool:
        """
        A user is authenticated if token is in the cache
        """
        token = self._token_encrypt.decrypt(access_token)
        cached_token = await self._token_cache.get(token["sub"])
        return cached_token is not None

    async def authenticate(self, user_auth: model.UserAuth) -> str:
        token = self.create_access_token(user_auth.entity_id, user_auth.role)
        await self._token_cache.set(user_auth.entity_id, token)
        return token

    def create_access_token(self, user_id: str, user_role: model.UserRoles) -> str:
        now_ = utcts_factory()
        token = model.AccessToken(
            sub=user_id,
            exp=now_ + timedelta(minutes=self._ttl_m),
            nbf=now_,
            iat=now_,
            role=user_role,
        )

        return self._token_encrypt.encrypt(token)

    async def revoke_token(self, user_id: str, token: str) -> None:
        """
        Revoke token from user
        """
        await self._token_cache.remove(user_id)

    @classmethod
    def build(cls, settings: Settings) -> "Authenticator":
        cache = factory.get_localcache()
        return cls(
            token_cache=cache,
            token_encrypt=factory.get_token_encrypt(settings=settings),
            token_ttl=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES,
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
        producer: mq.MessageProducer[IEvent],
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

        if not user.is_active:
            ...

        user.login()

        logger.success(f"User {user.entity_id} logged in")
        return await self._auth.authenticate(user)

    async def is_user_authenticated(self, access_token: str) -> bool:
        # TODO: check if user is active
        return await self._auth.is_access_token_valid(access_token=access_token)

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
