from datetime import datetime, timedelta

from src.app import factory
from src.app.auth import repository
from src.app.auth.model import AccessToken
from src.domain.config import Settings, get_setting
from src.domain.encrypt import create_jwt


class Authenticator:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self._is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    def authenticate(self):
        self._is_authenticated = True


class AuthService:
    def __init__(self, user_repo: repository.UserRepository):
        self._user_repo = user_repo
        self.settings = get_setting().security

    def create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token = AccessToken(expire_at=expire, user_id=user_id)
        encoded_jwt = create_jwt(
            token.asdict(), self.settings.SECRET_KEY, self.settings.ALGORITHM
        )
        return encoded_jwt

    async def authenticate(self, email: str, password: str) -> repository.User:
        ...

    async def is_active(self, user: repository.User) -> bool:
        ...

    async def login(self, email: str, password: str) -> Authenticator:
        if not email:
            raise ValueError("email is required")

        user = await self._user_repo.search_user_by_email(email)

        if not user:
            raise ValueError("user not found")

        if not user.user_info.verify_password(password):
            raise ValueError("Invalid password")

        # logger.success(f"User {user} logged in")
        auth = Authenticator(user_id=user.entity_id)
        auth.authenticate()
        return auth

    async def find_user(self, username: str, useremail: str) -> repository.User | None:
        """
        make sure user does not exist
        """
        user_or_none = await self._user_repo.search_user_by_email(useremail)
        return user_or_none

    async def create_user(
        self, username: str, useremail: str, password: str
    ) -> repository.User:
        """
        make sure user does not exist
        """
        user = repository.User.create(username, useremail, password)
        await self._user_repo.add(user)
        return user

    @classmethod
    def build(cls, settings: Settings) -> "AuthService":
        aioengine = factory.get_async_engine(settings)
        user_repo = repository.UserRepository(aioengine)
        return cls(user_repo=user_repo)
