import typing as ty

from fastapi import APIRouter, Depends

from askgpt.app.api.dependencies import ParsedToken
from askgpt.app.api.model import RequestBody, ResponseData
from askgpt.app.auth.errors import InvalidCredentialError, UserNotFoundError
from askgpt.app.auth.model import UserAuth
from askgpt.app.factory import AuthService, auth_service_factory
from askgpt.domain.base import SupportedGPTs

user_router = APIRouter(prefix="/users")

Service = ty.Annotated[AuthService, Depends(auth_service_factory)]


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


@user_router.get("/")
async def find_user_by_email(service: Service, email: str) -> PublicUserInfo:
    user = await service.find_user(email)
    if not user:
        raise UserNotFoundError(user_id=email)

    return PublicUserInfo.from_auth(user)


@user_router.get("/me")
async def get_public_user(service: Service, token: ParsedToken) -> PublicUserInfo:
    user = await service.get_current_user(token)
    return PublicUserInfo.from_auth(user)


@user_router.get("/{user_id}")
async def get_user_detail(
    service: Service, user_id: str, token: ParsedToken
) -> UserAuth | None:
    "Return private user info"
    if user_id != token.sub:
        raise InvalidCredentialError("user id does not match with credentials")
    user = await service.get_user(user_id)
    return user


@user_router.delete("/{user_id}")
async def delete_user(service: Service, token: ParsedToken):
    await service.deactivate_user(token.sub)


class CreateNewKey(RequestBody):
    api_key: str
    api_type: SupportedGPTs = "openai"


@user_router.post("/apikeys")
async def create_new_key(service: Service, r: CreateNewKey, token: ParsedToken):
    "add new api key to user, NOT idempotent"
    # may be we should keep a hash of the api_key 
    await service.add_api_key(user_id=token.sub, api_key=r.api_key, api_type=r.api_type)
