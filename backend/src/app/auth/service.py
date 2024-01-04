from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from src.app.auth import errors, model, repository
from src.domain._log import logger
from src.domain.config import Settings
from src.domain.interface import IEvent
from src.domain.model.base import str_to_snake, utcts_factory, uuid_factory
from src.infra import cache, encrypt, mq


class TokenRegistry:
    def __init__(self, token_cache: cache.RedisCache, keyspace: cache.KeySpace):
        self._cache = token_cache
        self._keyspace = keyspace(str_to_snake(self.__class__.__name__))

    def token_key(self, user_id: str) -> str:
        return self._keyspace(user_id).key

    async def is_token_valid(self, user_id: str, token: str) -> bool:
        return await self._cache.sismember(self.token_key(user_id), token)

    async def register_token(self, user_id: str, token: str) -> None:
        """
        Register token to user
        """
        await self._cache.sadd(self.token_key(user_id), token)

    async def revoke_tokens(self, user_id: str, token: str) -> None:
        """
        Revoke tokens from user
        """
        await self._cache.remove(user_id)


class AuthService:
    def __init__(
        self,
        user_repo: repository.UserRepository,
        token_registry: TokenRegistry,
        token_encrypt: encrypt.Encrypt,
        producer: mq.MessageProducer[IEvent],
        security_settings: Settings.Security,
    ):
        self._user_repo = user_repo
        self._token_registry = token_registry
        self._token_encrypt = token_encrypt
        self._producer = producer
        self._security_settings = security_settings

    @asynccontextmanager
    async def lifespan(self):
        try:
            yield self
        finally:
            await self._user_repo._aioengine.dispose()
            await self._token_registry._cache.close()

    @property
    def user_repo(self):
        return self._user_repo

    def _create_access_token(self, user_id: str, user_role: model.UserRoles) -> str:
        now_ = utcts_factory()
        exp = now_ + timedelta(
            minutes=self._security_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token = model.AccessToken(
            sub=user_id,
            exp=exp,
            nbf=now_,
            iat=now_,
            role=user_role,
        )

        return self._token_encrypt.encrypt_jwt(token)

    async def login(self, email: str, password: str) -> str:
        user = await self._user_repo.search_user_by_email(email)

        if user is None:
            raise errors.UserNotFoundError(user_email=email)

        if not user.user_info.verify_password(password):
            raise errors.InvalidPasswordError("Invalid password")

        if not user.is_active:
            raise errors.UserNotFoundError(user_email=email)

        user.login()

        logger.success(f"User {user.entity_id} logged in")
        return self._create_access_token(user.entity_id, user.role)

    async def find_user(self, useremail: str) -> model.UserAuth | None:
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    async def signup_user(self, user_name: str, email: str, password: str) -> str:
        user = await self.find_user(email)
        if user is not None:
            raise errors.UserAlreadyExistError(f"user {email} already exist")

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

    async def add_api_key(self, user_id: str, api_key: str, api_type: str) -> None:
        user = await self._user_repo.get(user_id)
        if user is None:
            raise errors.UserNotFoundError(user_email=user_id)

        encrypted_key = self._token_encrypt.encrypt_string(api_key).decode()

        event = model.UserAPIKeyAdded(
            user_id=user_id,
            api_key=encrypted_key,
            api_type=api_type,
        )

        # NOTE: api key will changed when encrypted, leading to multiple rows of same api key
        await self._user_repo.add_api_key_for_user(user_id, encrypted_key, api_type)
        await self._producer.publish(event)

    async def get_user_detail(self, user_id: str) -> model.UserAuth | None:
        return await self._user_repo.get(user_id)
