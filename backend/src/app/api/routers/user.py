import typing as ty

from fastapi import APIRouter, Depends
from src.app.api.dependencies import AccessToken, parse_access_token
from src.app.api.model import RequestBody
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.factory import AuthService, auth_service_factory
from src.domain.base import SupportedGPTs

user_router = APIRouter(prefix="/users")

Service = ty.Annotated[AuthService, Depends(auth_service_factory)]
ParsedToken = ty.Annotated[AccessToken, Depends(parse_access_token)]


class PublicUserInfo(ty.TypedDict):
    user_id: str
    user_name: str
    email: str


def auth_to_public(auth: UserAuth) -> PublicUserInfo:
    return PublicUserInfo(
        user_id=auth.entity_id,
        user_name=auth.credential.user_name,
        email=auth.credential.user_email,
    )


class UserAddAPIRequest(RequestBody):
    api_key: str
    api_type: SupportedGPTs = "openai"


@user_router.get("/")
async def find_user_by_email(service: Service, email: str) -> PublicUserInfo | None:
    user = await service.find_user(email)
    if not user:
        raise UserNotFoundError(user_id=email)

    return auth_to_public(user)


@user_router.get("/me")
async def get_public_user(service: Service, token: ParsedToken):
    user = await service.get_current_user(token)
    return auth_to_public(user)


@user_router.get("/{user_id}")
async def get_user_detail(
    service: Service, user_id: str, token: ParsedToken
) -> UserAuth | None:
    "Private user info"
    if not user_id == token.sub:
        raise InvalidCredentialError("user does not match with credentials")
    user = await service.get_user(user_id)
    return user


@user_router.delete("/{user_id}")
async def delete_user(service: Service, token: ParsedToken):
    await service.deactivate_user(token.sub)


@user_router.post("/apikeys")
async def add_api_key(service: Service, req: UserAddAPIRequest, token: ParsedToken):
    await service.add_api_key(
        user_id=token.sub, api_key=req.api_key, api_type=req.api_type
    )
