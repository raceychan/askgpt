from fastapi import APIRouter, Depends

from src.app.auth.model import CreateUserRequest
from src.app.auth.service import AuthService
from src.domain.config import get_setting

auth = APIRouter(prefix="/auth")


def get_auth_service():
    settings = get_setting()
    return AuthService.build(settings)


@auth.get("/login")
async def login(
    email: str, password: str, service: AuthService = Depends(get_auth_service)
) -> dict[str, str]:
    token = await service.login(email=email, password=password)
    res = {
        "access_token": token,
        "token_type": "bearer",
    }
    return res


@auth.post("/signup")
async def create_user(
    create_req: CreateUserRequest,
    service: AuthService = Depends(get_auth_service),
):
    await service.create_user(create_req)
