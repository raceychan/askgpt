from askgpt.api.model import EmptyResponse
from askgpt.app.auth.api import auth_router
from askgpt.app.gpt.api import gpt_router, sessions
from askgpt.app.user.api import user_router
from fastapi import APIRouter
from fastapi.routing import APIRoute


def route_id_factory(route: APIRoute):
    route_tag = route.tags[0] if route.tags else route.path.split("/")[-1]
    return f"{route_tag}-{route.name}"


def health_check():
    return EmptyResponse.OK


health_router = APIRouter(prefix="/health")
health_router.get("/")(health_check)

# include sub routers
gpt_router.include_router(sessions, tags=["sessions"])

feature_router = APIRouter()
feature_router.include_router(health_router, tags=["health"])
feature_router.include_router(auth_router, tags=["auth"])
feature_router.include_router(user_router, tags=["user"])
feature_router.include_router(gpt_router, tags=["gpt"])
