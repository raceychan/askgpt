import typing as ty

from askgpt.app.auth._errors import InvalidCredentialError, UserNotFoundError
from askgpt.app.auth.api import ParsedToken
from askgpt.app.user._model import UserInfo
from askgpt.app.user.service import UserService
from askgpt.domain.config import dg
from fastapi import APIRouter, Depends

user_router = APIRouter(prefix="/users")
Service = ty.Annotated[UserService, Depends(lambda: dg.resolve(UserService))]


@user_router.get("/")
async def find_user_by_email(service: Service, email: str) -> UserInfo:
    user = await service.find_user(email)
    if not user:
        raise UserNotFoundError(user_id=email)

    return user


@user_router.get("/{user_id}")
async def get_user_detail(
    service: Service, user_id: str, token: ParsedToken
) -> UserInfo | None:
    "Return private user info"
    if user_id != token.sub:
        raise InvalidCredentialError("user id does not match with credentials")
    user = await service.get_user(user_id)
    return user
