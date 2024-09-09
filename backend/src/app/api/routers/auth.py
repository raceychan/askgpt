import typing as ty

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from src.app.api.model import RequestBody
from src.app.api.response import RedirectResponse
from src.app.factory import AuthService, auth_service_factory
from src.domain.base import EMPTY_STR

auth_router = APIRouter(prefix="/auth")


Service = ty.Annotated[AuthService, Depends(auth_service_factory)]
LoginForm = ty.Annotated[OAuth2PasswordRequestForm, Depends()]


class TokenResponse(ty.TypedDict):
    access_token: str
    token_type: str


class CreateUserRequest(RequestBody):
    user_name: str = EMPTY_STR
    email: EmailStr
    password: str


@auth_router.post("/login")
async def login(service: Service, login_form: LoginForm) -> TokenResponse:
    token = await service.login(email=login_form.username, password=login_form.password)
    return TokenResponse(access_token=token, token_type="bearer")


@auth_router.post("/signup")
async def signup(service: Service, req: CreateUserRequest) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    await service.signup_user(req.user_name, req.email, req.password)
    return RedirectResponse(f"/v1/users?email={req.email}", status_code=303)
