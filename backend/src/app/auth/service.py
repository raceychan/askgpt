from datetime import datetime, timedelta

from src.adapters import cache, queue
from src.app.auth import errors, model, repository
from src.domain.config import Settings
from src.domain.interface import IEvent
from src.domain.model.base import utcts_factory, uuid_factory
from src.infra import security


class TokenRegistry:
    """
    a registry for refresh-token, validated by redis
    """

    def __init__(self, token_cache: cache.Cache[str, str], keyspace: cache.KeySpace):
        self._cache = token_cache
        self._keyspace = keyspace

    def token_key(self, user_id: str) -> str:
        return self._keyspace(user_id).key

    async def is_token_valid(self, user_id: str, token: str) -> bool:
        return await self._cache.sismember(self.token_key(user_id), token)

    async def register_token(self, user_id: str, token: str) -> None:
        await self._cache.sadd(self.token_key(user_id), token)

    async def revoke_tokens(self, user_id: str, token: str) -> None:
        await self._cache.remove(user_id)


class AuthService:
    # NOTE: we are ignoring the dual write problem here,
    # but we should solve it in next few commits
    def __init__(
        self,
        user_repo: repository.UserRepository,
        token_registry: TokenRegistry,
        token_encrypt: security.Encrypt,
        producer: queue.MessageProducer[IEvent],
        security_settings: Settings.Security,
    ):
        self._user_repo = user_repo
        self._token_registry = token_registry
        self._token_encrypt = token_encrypt
        self._producer = producer
        self._security_settings = security_settings

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
            raise errors.UserNotFoundError(user_id=email)

        if not user.user_info.verify_password(password):
            raise errors.InvalidPasswordError("Invalid password")

        if not user.is_active:
            raise errors.UserNotFoundError(user_id=email)

        user.login()

        access_token = self._create_access_token(user.entity_id, user.role)
        return access_token

    async def find_user(self, email: str) -> model.UserAuth | None:
        user_or_none = await self._user_repo.search_user_by_email(email)
        return user_or_none

    async def signup_user(self, user_name: str, email: str, password: str) -> str:
        user = await self.find_user(email)
        if user is not None:
            raise errors.UserAlreadyExistError(f"user {email} already exist")

        hash_password = security.hash_password(password.encode())
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

    async def deactivate_user(self, user_id: str) -> None:
        user = await self._user_repo.get(user_id)
        if user is None:
            raise errors.UserNotFoundError(user_id=user_id)
        e = model.UserDeactivated(user_id=user_id)
        user.apply(e)
        await self._user_repo.remove(user.entity_id)
        await self._producer.publish(e)

    async def add_api_key(self, user_id: str, api_key: str, api_type: str) -> None:
        """
        TODO: calculate the hash_value of api_key so that we can avoid duplicated api_key
        key_hash = hash(api_key)
        is_duplicate = await self._user_repo.check_for_key_duplicate(user_id, key_hash)
        if is_duplicate:
            raise DuplicatedAPIKeyError
        """

        user = await self._user_repo.get(user_id)
        if user is None:
            raise errors.UserNotFoundError(user_id=user_id)

        encrypted_key = self._token_encrypt.encrypt_string(api_key).decode()

        user_api_added = model.UserAPIKeyAdded(
            user_id=user_id,
            api_key=encrypted_key,
            api_type=api_type,
        )

        await self._user_repo.add_api_key_for_user(user_id, encrypted_key, api_type)
        await self._producer.publish(user_api_added)

    async def get_user(self, user_id: str) -> model.UserAuth | None:
        return await self._user_repo.get(user_id)

    async def get_current_user(self, token: str)->model.UserAuth:
        try:
            payload = self._token_encrypt.decrypt_jwt(token)
            data = model.AccessToken.model_validate(payload)
        except (security.JWTError, security.ValidationError):
            raise errors.InvalidCredentialError

        user_id = data.sub
        user = await self.get_user(user_id)
        if not user:
            raise errors.UserNotFoundError(user_id=user_id)
        return user

            