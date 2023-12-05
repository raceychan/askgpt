from fastapi import APIRouter

from src.app.auth.api import auth
from src.app.gpt.api import gpt

api_router = APIRouter()
api_router.include_router(auth, tags=["auth"])
api_router.include_router(gpt, tags=["gpt"])
