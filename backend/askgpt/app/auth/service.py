from datetime import datetime, timedelta

from askgpt.adapters.cache import Cache, KeySpace
from askgpt.app.auth.errors import (
    DuplicatedAPIKeyError,
    InvalidPasswordError,
    UserAlreadyExistError,
    UserInactiveError,
    UserNotFoundError,
)
from askgpt.app.auth.model import (
    AccessToken,
    UserAPIKeyAdded,
    UserAuth,
    UserCredential,
    UserDeactivated,
    UserRoles,
    UserSignedUp,
)
from askgpt.app.auth.repository import AuthRepository
from askgpt.domain.config import Settings
from askgpt.domain.model.base import utc_now, uuid_factory
from askgpt.infra import security
from askgpt.infra.eventstore import EventStore


# from askgpt.adapters import queue
class TokenRegistry:
    """
    a registry for access-token, validated by redis
    """

    def __init__(self, token_cache: Cache[str, str], keyspace: KeySpace):
        self._cache = token_cache
        self._keyspace = keyspace

    def token_key_by(self, user_id: str) -> str:
        return self._keyspace(user_id).key

    async def is_token_valid(self, user_id: str, token: str) -> bool:
        return await self._cache.sismember(self.token_key_by(user_id), token)

    async def register_token(self, user_id: str, token: str) -> None:
        await self._cache.sadd(self.token_key_by(user_id), token)

    async def revoke_tokens(self, user_id: str, token: str) -> None:
        await self._cache.remove(user_id)


class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        token_registry: TokenRegistry,
        encryptor: security.Encryptor,
        eventstore: EventStore,
        security_settings: Settings.Security,
    ):
        self._uow = auth_repo.uow
        self._auth_repo = auth_repo
        self._token_registry = token_registry
        self._encryptor = encryptor
        self._eventstore = eventstore
        self._security_settings = security_settings

    def _create_access_token(self, user_id: str, user_role: UserRoles) -> str:
        # TODO: create a separate infra <TokenEncrypt> for this
        now_ = utc_now()
        exp = now_ + timedelta(
            minutes=self._security_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token = AccessToken(
            sub=user_id,
            exp=exp,
            nbf=now_,
            iat=now_,
            role=user_role,
        )

        return self._encryptor.encrypt_jwt(token)

    async def signup_user(self, user_name: str, email: str, password: str) -> None:
        async with self._uow.trans():
            user = await self._auth_repo.search_user_by_email(email)
            if user is not None:
                raise UserAlreadyExistError(email=email)

        hash_password = security.hash_password(password.encode())
        user_info = UserCredential(
            user_name=user_name, user_email=email, hash_password=hash_password
        )
        user_signed_up = UserSignedUp(
            user_id=uuid_factory(),
            credential=user_info,
            last_login=datetime.utcnow(),
        )
        user_auth = UserAuth.apply(user_signed_up)

        async with self._uow.trans():
            await self._auth_repo.add(user_auth)
            await self._eventstore.add(user_signed_up)

    async def add_api_key(self, user_id: str, api_key: str, api_type: str) -> None:
        async with self._uow.trans():
            user = await self._auth_repo.get(user_id)
            if user is None:
                raise UserNotFoundError(user_id=user_id)

        encrypted_key = self._encryptor.encrypt_string(api_key).decode()
        idem_id = self._encryptor.hash_string(api_type + api_key).hex()
        user_api_added = UserAPIKeyAdded(
            user_id=user_id,
            api_key=encrypted_key,
            api_type=api_type,
            idem_id=idem_id,
        )

        try:
            async with self._uow.trans():
                await self._auth_repo.add_api_key_for_user(
                    user_id, encrypted_key, api_type, idem_id
                )
                await self._eventstore.add(user_api_added)
        except Exception as e:
            # TODO: catch specific error
            raise DuplicatedAPIKeyError(api_type=api_type) from e

    async def list_api_keys(self, user_id: str, api_type: str) -> tuple[str, ...]:
        async with self._uow.trans():
            encrypted_keys = await self._auth_repo.get_api_keys_for_user(
                user_id=user_id, api_type=api_type
            )

        api_keys = tuple(self._encryptor.decrypt_string(key) for key in encrypted_keys)
        return api_keys

    async def login(self, email: str, password: str) -> str:
        async with self._uow.trans():
            user = await self._auth_repo.search_user_by_email(email)

        if user is None:
            raise UserNotFoundError(user_id=email)

        if not user.credential.verify_password(password):
            raise InvalidPasswordError("Invalid password")

        if not user.is_active:
            raise UserInactiveError(user_id=email)

        user.login()

        access_token = self._create_access_token(user.entity_id, user.role)
        return access_token

    async def get_current_user(self, token: AccessToken) -> UserAuth:
        user_id = token.sub
        async with self._uow.trans():
            user = await self._auth_repo.get(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user

    async def deactivate_user(self, user_id: str):
        async with self._uow.trans():
            user = await self._auth_repo.get(user_id)
            if user is None:
                raise UserNotFoundError(user_id=user_id)
            e = UserDeactivated(user_id=user_id)
            user.apply(e)
            await self._auth_repo.remove(user.entity_id)
            await self._eventstore.add(e)
