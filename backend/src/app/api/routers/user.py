
import typing as ty

from fastapi import APIRouter, Depends
from pydantic import EmailStr
from src.app.api.dependencies import AccessToken, parse_access_token
from src.app.api.model import RequestBody
from src.app.auth.errors import InvalidCredentialError, UserNotFoundError
from src.app.auth.model import UserAuth
from src.app.factory import app_service_locator
from src.domain.base import EMPTY_STR, SupportedGPTs

user_router = APIRouter(prefix="/users")



class PublicUserInfo(ty.TypedDict):
    user_id: str
    user_name: str
    email: str



class UserAddAPIRequest(RequestBody):
    api_key: str
    api_type: SupportedGPTs = "openai"


@user_router.get("/")
async def find_user_by_email(email: str) -> PublicUserInfo | None:
    user = await app_service_locator.auth_service.find_user(email)
    if not user:
        raise UserNotFoundError(user_id=email)

    return PublicUserInfo(
        user_id=user.entity_id,
        user_name=user.user_info.user_name,
        email=user.user_info.user_email,
    )



@user_router.get("/{user_id}")
async def user_detail(
    user_id: str, token: AccessToken = Depends(parse_access_token)
) -> UserAuth | None:
    "Private user info"
    if not user_id == token.sub:
        raise InvalidCredentialError("user does not match with credentials")
    user = await app_service_locator.auth_service.get_user(user_id)
    return user


@user_router.delete("/{user_id}")
async def delete_user(user_id: str, token: AccessToken = Depends(parse_access_token)):
    await app_service_locator.auth_service.deactivate_user(token.sub)


@user_router.post("/apikeys")
async def add_api_key(
    req: UserAddAPIRequest,
    token: AccessToken = Depends(parse_access_token),
):
    await app_service_locator.auth_service.add_api_key(
        user_id=token.sub, api_key=req.api_key, api_type=req.api_type
    )

