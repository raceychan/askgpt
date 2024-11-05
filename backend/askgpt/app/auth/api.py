import typing as ty

from askgpt.api.model import EmptyResponse, RequestBody, ResponseData
from askgpt.app.auth_factory import AuthService, auth_service_resolver
from askgpt.domain.types import SupportedGPTs
from askgpt.helpers.string import EMPTY_STR
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr

from ._model import AccessToken, UserAuth

auth_router = APIRouter(prefix="/auth")


Service = ty.Annotated[AuthService, Depends(auth_service_resolver)]
LoginForm = ty.Annotated[OAuth2PasswordRequestForm, Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def parse_access_token(
    service: Service, token: str = Depends(oauth2_scheme)
) -> AccessToken:
    return service.decrypt_access_token(token)


ParsedToken = ty.Annotated[AccessToken, Depends(parse_access_token)]


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


@auth_router.delete("/{user_id}", status_code=200)
async def delete_user(service: Service, token: ParsedToken):
    await service.deactivate_user(token.sub)
    return EmptyResponse.OK


class CreateNewKey(RequestBody):
    api_key: str
    key_name: str
    api_type: SupportedGPTs = "openai"


# should be /user/apikeys
# POST /user/apikeys -> create new key


@auth_router.post("/apikeys", status_code=201)
async def create_new_key(service: Service, token: ParsedToken, r: CreateNewKey):
    await service.add_api_key(
        user_id=token.sub, api_key=r.api_key, api_type=r.api_type, key_name=r.key_name
    )
    return EmptyResponse.Created


class PublicAPIKey(ty.TypedDict):
    key_name: str
    key_type: str
    key: str


@auth_router.get("/apikeys")
async def list_keys(
    service: Service,
    token: ParsedToken,
    api_type: SupportedGPTs | None = None,
    as_secret: bool = True,
) -> list[PublicAPIKey]:
    keys = await service.list_api_keys(
        user_id=token.sub,
        api_type=api_type,
        as_secret=as_secret,
    )
    return [
        PublicAPIKey(key_name=name, key_type=type, key=key) for name, type, key in keys
    ]


@auth_router.delete("/apikeys/{key_name}", status_code=200)
async def remove_key(service: Service, token: ParsedToken, key_name: str):
    row_count = await service.remove_api_key(user_id=token.sub, key_name=key_name)
    return EmptyResponse.OK if row_count > 0 else EmptyResponse.NotFound
