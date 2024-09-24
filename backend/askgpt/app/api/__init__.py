"""
web API layer, including all the endpoints and logic related to them.
"""

from fastapi.routing import APIRoute

from askgpt.app.api.error_handlers import (
    add_exception_handlers as add_exception_handlers,
)
from askgpt.app.api.middleware import add_middlewares as add_middlewares


def route_id_factory(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"
