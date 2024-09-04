from fastapi import APIRouter
from src.app.api.routers import auth, gpt, llm, user

api_router = APIRouter()
gpt.gpt_router.include_router(gpt.openai_router)

api_router.include_router(auth.auth_router, tags=["auth"])
api_router.include_router(user.user_router, tags=["user"])
api_router.include_router(gpt.gpt_router, tags=["gpt"])
api_router.include_router(llm.llm_router, tags=["llm"])
