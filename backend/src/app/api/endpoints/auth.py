import typing as ty

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse, redirect
from src.app.api.validation import AccessToken, parse_access_token
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.auth.service import AuthService
from src.domain.config import get_setting

auth_router = APIRouter(prefix="/auth")
user_router = APIRouter(prefix="/users")


service = AuthService.from_settings(get_setting())


class TokenResponse(ty.TypedDict):
    access_token: str
    token_type: str


class PublicUserInfo(ty.TypedDict):
    user_id: str
    user_name: str
    email: str


class CreateUserRequest(RequestBody):
    user_name: str = ""
    email: EmailStr
    password: str


class UserAddAPIRequest(RequestBody):
    api_key: str
    api_type: ty.Literal["openai"] = "openai"


@auth_router.post("/login")
async def login(login_form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    email = login_form.username
    token = await service.login(email=email, password=login_form.password)
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def create_user(req: CreateUserRequest) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    user_id = await service.signup_user(req.user_name, req.email, req.password)
    return redirect(user_router, user_id)


@user_router.get("/{user_id}")
async def user_detail(
    user_id: str, token: AccessToken = Depends(parse_access_token)
) -> UserAuth | None:
    "Private user info"
    if not user_id == token.sub:
        raise InvalidCredentialError("user does not match with credentials")
    user = await service.user_repo.get(user_id)
    return user


@user_router.post("/apikeys")
async def add_api_key(
    req: UserAddAPIRequest, token: AccessToken = Depends(parse_access_token)
):
    await service.add_api_key(
        user_id=token.sub, api_key=req.api_key, api_type=req.api_type
    )


@user_router.get("/")
async def find_user_by_email(email: str) -> PublicUserInfo | None:
    user = await service.user_repo.search_user_by_email(email)
    if not user:
        raise UserNotFoundError("user not found")

    return PublicUserInfo(
        user_id=user.entity_id,
        user_name=user.user_info.user_name,
        email=user.user_info.user_email,
    )
