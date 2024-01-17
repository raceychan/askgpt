import typing as ty

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from src.app.api.dependencies import AccessToken, parse_access_token
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.factory import ApplicationServices
from src.domain.base import EMPTY_STR, SupportedGPTs

auth_router = APIRouter(prefix="/auth")
user_router = APIRouter(prefix="/users")


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
    api_type: SupportedGPTs = "openai"


@auth_router.post("/login")
async def login(login_form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    token = await ApplicationServices.auth_service.login(
        email=login_form.username, password=login_form.password
    )
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def signup_user(req: CreateUserRequest) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    await ApplicationServices.auth_service.signup_user(
        req.user_name, req.email, req.password
    )
    return RedirectResponse(f"/v1/users?email={req.email}", status_code=303)


@user_router.get("/{user_id}")
async def user_detail(
    user_id: str, token: AccessToken = Depends(parse_access_token)
) -> UserAuth | None:
    "Private user info"
    if not user_id == token.sub:
        raise InvalidCredentialError("user does not match with credentials")
    user = await ApplicationServices.auth_service.get_user(user_id)
    return user


@user_router.delete("/{user_id}")
async def delete_user(user_id: str, token: AccessToken = Depends(parse_access_token)):
    await ApplicationServices.auth_service.deactivate_user(token.sub)


@user_router.post("/apikeys")
async def add_api_key(
    req: UserAddAPIRequest,
    token: AccessToken = Depends(parse_access_token),
):
    await ApplicationServices.auth_service.add_api_key(
        user_id=token.sub, api_key=req.api_key, api_type=req.api_type
    )


@user_router.get("/")
async def find_user_by_email(email: str) -> PublicUserInfo | None:
    user = await ApplicationServices.auth_service.find_user(email)
    if not user:
        raise UserNotFoundError(user_email=email)

    return PublicUserInfo(
        user_id=user.entity_id,
        user_name=user.user_info.user_name,
        email=user.user_info.user_email,
    )
