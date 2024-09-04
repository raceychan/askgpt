import typing as ty

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from src.app.api.dependencies import AccessToken, parse_access_token
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.factory import service_locator
from src.domain.base import EMPTY_STR, SupportedGPTs

auth_router = APIRouter(prefix="/auth")


class TokenResponse(ty.TypedDict):
    access_token: str
    token_type: str


class CreateUserRequest(RequestBody):
    user_name: str = EMPTY_STR
    email: EmailStr
    password: str


@auth_router.post("/login")
async def login(login_form: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    token = await service_locator.auth_service.login(
        email=login_form.username, password=login_form.password
    )
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def signup_user(req: CreateUserRequest) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    await service_locator.auth_service.signup_user(
        req.user_name, req.email, req.password
    )
    return RedirectResponse(f"/v1/users?email={req.email}", status_code=303)
