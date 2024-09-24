import typing as ty

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from askgpt.app.api.model import RequestBody, ResponseData
from askgpt.app.factory import AuthService, auth_service_factory
from askgpt.domain.base import EMPTY_STR

auth_router = APIRouter(prefix="/auth")


Service = ty.Annotated[AuthService, Depends(auth_service_factory)]
LoginForm = ty.Annotated[OAuth2PasswordRequestForm, Depends()]


class TokenResponse(ResponseData):
    access_token: str
    token_type: ty.Literal["bearer"] = "bearer"


@auth_router.post("/login")
async def login(service: Service, login_form: LoginForm) -> TokenResponse:
    token = await service.login(email=login_form.username, password=login_form.password)
    return TokenResponse(access_token=token)


class SignUp(RequestBody):
    user_name: str = EMPTY_STR
    email: EmailStr
    password: str


@auth_router.post("/signup")
async def signup(service: Service, r: SignUp) -> RedirectResponse:
    "Request will be redirected to user route for user info"
    await service.signup_user(r.user_name, r.email, r.password)
    return RedirectResponse(f"/v1/users?email={r.email}", status_code=303)
