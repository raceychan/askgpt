from fastapi import APIRouter
from fastapi.responses import Response
from fastapi.routing import APIRoute

from askgpt.app.api.routers import auth, gpt, user

gpt.gpt_router.include_router(gpt.openai_router)


def route_id_factory(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def health_check():
    return Response(status_code=200)


health_router = APIRouter(prefix="/health")
health_router.get("/")(health_check)

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth.auth_router, tags=["auth"])
api_router.include_router(user.user_router, tags=["user"])
api_router.include_router(gpt.gpt_router, tags=["gpt"])
# api_router.include_router(llm.llm_router, tags=["llm"])
