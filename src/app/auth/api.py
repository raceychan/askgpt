from fastapi import APIRouter, HTTPException

accounts = APIRouter(prefix="/accounts")

import typing as ty

from src.app.auth.service import AuthService


@accounts.get("/login")
async def login(auth: AuthService, form_data: ty.Any):
    user = await auth.authenticate(
        email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not await auth.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    res = {
        "access_token": auth.create_access_token(user.entity_id),
        "token_type": "bearer",
    }
    return res


@accounts.post("/signup/user")
def create_user():
    ...
