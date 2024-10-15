from fastapi import APIRouter
from fastapi.responses import Response
from fastapi.routing import APIRoute

from askgpt.app.auth import route as auth_route
from askgpt.app.gpt import route as gpt_route
from askgpt.app.user import route as user_route


def route_id_factory(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def health_check():
    return Response(status_code=200)


health_router = APIRouter(prefix="/health")
health_router.get("/")(health_check)

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_route.auth_router, tags=["auth"])
api_router.include_router(user_route.user_router, tags=["user"])
api_router.include_router(gpt_route.gpt_router, tags=["gpt"])
