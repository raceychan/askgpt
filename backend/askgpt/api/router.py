from askgpt.app.auth.route import api_key_router, auth_router
from askgpt.app.gpt.route import gpt_router, openai_router
from askgpt.app.user.route import user_router
from fastapi import APIRouter
from fastapi.responses import Response
from fastapi.routing import APIRoute


def route_id_factory(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def health_check():
    return Response(status_code=200)


health_router = APIRouter(prefix="/health")
health_router.get("/")(health_check)

# include sub routers
auth_router.include_router(api_key_router, tags=["api_key"])
gpt_router.include_router(openai_router, tags=["openai"])


feature_router = APIRouter()
feature_router.include_router(health_router, tags=["health"])
feature_router.include_router(auth_router, tags=["auth"])
feature_router.include_router(user_router, tags=["user"])
feature_router.include_router(gpt_router, tags=["gpt"])
