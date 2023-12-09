from typing import TypedDict

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from starlette import status

from src.app.api.model import RequestBody
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


@auth_router.post("/login")
async def login(req: UserLoginRequest) -> TokenResponse:
    token = await service.login(req.email, req.password)
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def create_user(req: CreateUserRequest):
    "PRG pattern"
    user_id = await service.signup_user(req.user_name, req.email, req.password)
    return RedirectResponse(
        f"/v1/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER
    )


@user_router.get("/{user_id}")
async def get_user(user_id: str) -> UserAuth | None:
    user = await service.user_repo.get(user_id)
    return user
