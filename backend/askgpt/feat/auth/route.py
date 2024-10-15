import typing as ty

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from askgpt.domain.base import EMPTY_STR, SupportedGPTs
from askgpt.api.dependencies import ParsedToken
from askgpt.api.model import RequestBody, ResponseData
from askgpt.feat.auth.model import UserAuth
from askgpt.feat.factory import AuthService, auth_service_factory

auth_router = APIRouter(prefix="/auth")


Service = ty.Annotated[AuthService, Depends(auth_service_factory)]
LoginForm = ty.Annotated[OAuth2PasswordRequestForm, Depends()]


class TokenResponse(ResponseData):
    access_token: str
    token_type: ty.Literal["bearer"] = "bearer"


class PublicUserInfo(ResponseData):
    user_id: str
    user_name: str
    email: str

    @classmethod
    def from_auth(cls, auth: UserAuth) -> ty.Self:
        return cls(
            user_id=auth.entity_id,
            user_name=auth.credential.user_name,
            email=auth.credential.user_email,
        )


@auth_router.post("/login")
async def login(service: Service, login_form: LoginForm) -> TokenResponse:
    "Receive form data, return a JWT that client should keep locally"
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


@auth_router.get("/me")
async def get_public_user(service: Service, token: ParsedToken) -> PublicUserInfo:
    user = await service.get_current_user(token)
    return PublicUserInfo.from_auth(user)


class CreateNewKey(RequestBody):
    api_key: str
    api_type: SupportedGPTs = "openai"


@auth_router.post("/apikeys")
async def create_new_key(service: Service, r: CreateNewKey, token: ParsedToken):
    await service.add_api_key(user_id=token.sub, api_key=r.api_key, api_type=r.api_type)


@auth_router.delete("/{user_id}")
async def delete_user(service: Service, token: ParsedToken):
    await service.deactivate_user(token.sub)
