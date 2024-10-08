"""
web API layer, including all the endpoints and logic related to them.
"""

from fastapi.responses import Response
from fastapi.routing import APIRoute


def route_id_factory(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def health_check():
    return Response(status_code=200)
