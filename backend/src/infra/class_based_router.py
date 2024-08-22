# import inspect
# from collections.abc import Callable
# from typing import Any, TypeVar, get_type_hints

# from fastapi import APIRouter, Depends
# from pydantic.typing import is_classvar
# from starlette.routing import Route, WebSocketRoute


CBV_CLASS_KEY = "__cbv_class__"


# def cbv(router: APIRouter) -> Callable[[type[T]], type[T]]:
#     """
#     This function returns a decorator that converts the decorated into a class-based view for the provided router.

#     Any methods of the decorated class that are decorated as endpoints using the router provided to this function
#     will become endpoints in the router. The first positional argument to the methods (typically `self`)
#     will be populated with an instance created using FastAPI's dependency-injection.

#     For more detail, review the documentation at
#     https://fastapi-utils.davidmontague.xyz/user-guide/class-based-views/#the-cbv-decorator
#     """

#     def decorator(cls: type[T]) -> type[T]:
#         return _cbv(router, cls)

#     return decorator

import inspect

from fastapi import APIRouter
from starlette.routing import Route, WebSocketRoute
from typing import *

def cbv[T](router: APIRouter, cls: type[T]) -> type[T]:
    if not getattr(cls, CBV_CLASS_KEY, False):  # pragma: no cover
        old_init: Callable[..., Any] = cls.__init__
        old_signature = inspect.signature(old_init)
        old_parameters = list(old_signature.parameters.values())[
            1:
        ]  # drop `self` parameter
        new_parameters = [
            x
            for x in old_parameters
            if x.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]
        dependency_names: list[str] = []
        for name, hint in get_type_hints(cls).items():
            if is_classvar(hint):
                continue
            parameter_kwargs = {"default": getattr(cls, name, Ellipsis)}
            dependency_names.append(name)
            new_parameters.append(
                inspect.Parameter(
                    name=name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    annotation=hint,
                    **parameter_kwargs,
                )
            )
        new_signature = old_signature.replace(parameters=new_parameters)

        def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
            for dep_name in dependency_names:
                dep_value = kwargs.pop(dep_name)
                setattr(self, dep_name, dep_value)
            old_init(self, *args, **kwargs)

        setattr(cls, "__signature__", new_signature)
        setattr(cls, "__init__", new_init)
        setattr(cls, CBV_CLASS_KEY, True)

    cbv_router = APIRouter()
    function_members = inspect.getmembers(cls, inspect.isfunction)
    functions_set = {func for _, func in function_members}
    cbv_routes = [
        route
        for route in router.routes
        if isinstance(route, (Route, WebSocketRoute))
        and route.endpoint in functions_set
    ]
    for route in cbv_routes:
        router.routes.remove(route)
        _update_cbv_route_endpoint_signature(cls, route)
        cbv_router.routes.append(route)
    router.include_router(cbv_router)
    return cls


def _update_cbv_route_endpoint_signature(
    cls: type, route: Route | WebSocketRoute
) -> None:
    """
    Fixes the endpoint signature for a cbv route to ensure FastAPI performs dependency injection properly.
    """
    old_endpoint = route.endpoint
    old_signature = inspect.signature(old_endpoint)
    old_parameters: list[inspect.Parameter] = list(old_signature.parameters.values())
    old_first_parameter = old_parameters[0]
    new_first_parameter = old_first_parameter.replace(default=Depends(cls))
    new_parameters = [new_first_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY)
        for parameter in old_parameters[1:]
    ]
    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(route.endpoint, "__signature__", new_signature)


class ClassBasedRouter:
    def __init_subclass__(cls, router: APIRouter) -> None: ...
