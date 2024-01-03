import typing as ty

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from src.app.api.dependencies import AccessToken, parse_access_token
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse, redirect
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.factory import AuthService, get_auth_service
from src.domain.base import EMPTY_STR
from src.domain.config import Settings, get_setting

auth_router = APIRouter(prefix="/auth")
user_router = APIRouter(prefix="/users")


def auth_settings():
    return get_setting("settings.toml")


def auth_service(
    settings: ty.Annotated[Settings, Depends(auth_settings)]
) -> AuthService:
    return get_auth_service(settings)


ServiceDep = ty.Annotated[AuthService, Depends(auth_service)]


class TokenResponse(ty.TypedDict):
    access_token: str
    token_type: str


class PublicUserInfo(ty.TypedDict):
    user_id: str
    user_name: str
    email: str


class CreateUserRequest(RequestBody):
    user_name: str = EMPTY_STR
    email: EmailStr
    password: str


class UserAddAPIRequest(RequestBody):
    api_key: str
    api_type: ty.Literal["openai"] = "openai"


@auth_router.post("/login")
async def login(
    service: ServiceDep, login_form: OAuth2PasswordRequestForm = Depends()
) -> TokenResponse:
    email = login_form.username
    token = await service.login(email=email, password=login_form.password)
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def create_user(service: ServiceDep, req: CreateUserRequest) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    user_id = await service.signup_user(req.user_name, req.email, req.password)
    return redirect(user_router, user_id)


@user_router.get("/{user_id}")
async def user_detail(
    service: ServiceDep, user_id: str, token: AccessToken = Depends(parse_access_token)
) -> UserAuth | None:
    "Private user info"
    if not user_id == token.sub:
        raise InvalidCredentialError("user does not match with credentials")
    user = await service.user_repo.get(user_id)
    return user


@user_router.post("/apikeys")
async def add_api_key(
    service: ServiceDep,
    req: UserAddAPIRequest,
    token: AccessToken = Depends(parse_access_token),
):
    await service.add_api_key(
        user_id=token.sub, api_key=req.api_key, api_type=req.api_type
    )


@user_router.get("/")
async def find_user_by_email(service: ServiceDep, email: str) -> PublicUserInfo | None:
    user = await service.user_repo.search_user_by_email(email)
    if not user:
        raise UserNotFoundError("user not found")

    return PublicUserInfo(
        user_id=user.entity_id,
        user_name=user.user_info.user_name,
        email=user.user_info.user_email,
    )
