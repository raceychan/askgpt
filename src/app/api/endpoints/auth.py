from typing import TypedDict

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from starlette import status

from src.app.api.model import RequestBody
from src.app.api.validation import oauth2_scheme
from src.app.auth.errors import UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.auth.service import AuthService
from src.domain.config import get_setting

auth_router = APIRouter(prefix="/auth")
user_router = APIRouter(prefix="/users")


service = AuthService.build(get_setting())


class CreateUserRequest(RequestBody):
    user_name: str = ""
    email: EmailStr
    password: str


class UserLoginRequest(RequestBody):
    email: EmailStr
    password: str


class TokenResponse(TypedDict):
    access_token: str
    token_type: str


class PublicUserInfo(TypedDict):
    user_id: str
    user_name: str
    email: str


@auth_router.post("/login")
async def login(login_form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    email = login_form.username
    token = await service.login(email=email, password=login_form.password)
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def create_user(req: CreateUserRequest):
    "Request will be redirected to user route for user info"
    # TODO: user should be logged in after signup, return access_token
    user_id = await service.signup_user(req.user_name, req.email, req.password)
    return RedirectResponse(
        f"/v1/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@user_router.get("/{user_id}")
async def get_user(user_id: str) -> UserAuth | None:
    user = await service.user_repo.get(user_id)
    return user


@user_router.get("/")
async def find_user_by_email(
    email: str, token: str = Depends(oauth2_scheme)
) -> PublicUserInfo | None:
    user = await service.user_repo.search_user_by_email(email)
    if not user:
        raise UserNotFoundError("user not found")

    return PublicUserInfo(
        user_id=user.entity_id,
        user_name=user.user_info.user_name,
        email=user.user_info.user_email,
    )
