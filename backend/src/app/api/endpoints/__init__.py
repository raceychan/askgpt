from fastapi import APIRouter

from src.app.api.endpoints import auth, gpt

gpt.gpt_router.include_router(gpt.openai)

api_router = APIRouter()
api_router.include_router(auth.auth_router, tags=["auth"])
api_router.include_router(auth.user_router, tags=["user"])
api_router.include_router(gpt.gpt_router, tags=["openai"])
api_router.include_router(gpt.llm_router, tags=["llm"])
