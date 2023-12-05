from datetime import datetime

from src.app import factory
from src.app.auth import repository
from src.app.auth.model import AccessToken, CreateUserRequest, UserAuth, UserRoles
from src.app.error import ClientSideError
from src.app.model import UserInfo
from src.domain import encrypt
from src.domain._log import logger
from src.domain.config import Settings
from src.infra.cache import Cache, LocalCache


class Authenticator:
    """
    On every user request for content that might need authentication,
    ensure that token is in the user's Redis store i.e ${userId}-tokens. If the token is not in the Redis store, then it is not a valid token anymore.
    """

    def __init__(
        self,
        token_cache: Cache[str, str],
        security: Settings.Security,
    ):
        self._token_cache = token_cache
        self._secrete_key = security.SECRET_KEY
        self._encode_algo = security.ALGORITHM
        self._ttl_m = security.ACCESS_TOKEN_EXPIRE_MINUTES

    async def is_authenticated(self, access_token: str) -> bool:
        token = encrypt.decode_jwt(
            access_token, secret_key=self._secrete_key, algorithm=self._encode_algo
        )
        cached_token = await self._token_cache.get(token["user_id"])
        return bool(cached_token)

    async def authenticate(self, user_auth: UserAuth) -> str:
        """
        Use this to grant privilege to user, change its role
        """
        token = self.create_access_token(user_auth.entity_id, user_auth.role)
        await self._token_cache.set(user_auth.entity_id, token)
        return token

    def create_jwt(self, content: dict[str, str]):
        return encrypt.create_jwt(
            content, secret_key=self._secrete_key, algorithm=self._encode_algo
        )

    def create_access_token(self, user_id: str, user_role: UserRoles) -> str:
        token = AccessToken(ttl_m=self._ttl_m, user_id=user_id, role=user_role)
        encoded_jwt = self.create_jwt(token.asdict())
        return encoded_jwt

    async def revoke_token(self, user_id: str, token: str) -> None:
        """
        revoke token from user
        """
        await self._token_cache.remove(user_id)


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


class AuthService:
    def __init__(
        self, user_repo: repository.UserRepository, authenticator: Authenticator
    ):
        self._user_repo = user_repo
        self._auth = authenticator

    async def login(self, email: str, password: str) -> str:
        user = await self._user_repo.search_user_by_email(email)

        if user is None:
            raise UserNotFoundError("user not found")

        if not user.user_info.verify_password(password):
            raise InvalidPasswordError("Invalid password")

        user.login()

        logger.success(f"User {user} logged in")
        return await self._auth.authenticate(user)

    async def is_user_authenticated(self, access_token: str) -> bool:
        return await self._auth.is_authenticated(access_token=access_token)

    async def find_user(self, username: str, useremail: str) -> UserAuth | None:
        """
        make sure user does not exist
        """
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    async def create_user(self, req: CreateUserRequest) -> None:
        """
        make sure user does not exist
        """
        hash_password = encrypt.hash_password(req.password.encode())
        user_info = UserInfo(
            user_name=req.user_name, user_email=req.email, hash_password=hash_password
        )
        user_auth = UserAuth(user_info=user_info, last_login=datetime.utcnow())
        await self._user_repo.add(user_auth)

    @classmethod
    def build(cls, settings: Settings) -> "AuthService":
        aioengine = factory.get_async_engine(settings)
        user_repo = repository.UserRepository(aioengine)
        cache = LocalCache[str, str].from_singleton()
        return cls(
            user_repo=user_repo,
            authenticator=Authenticator(token_cache=cache, security=settings.security),
        )
