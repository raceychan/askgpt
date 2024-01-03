"""
a centralized place to store dependencies
push dependencies to exit stack when initializing them
pop dependencies from exit stack when exiting them
for every dependency, instantiate with a factory function

difference with fastapi.dependencies.Depends:
1. exit stack
2. this is for app-wide dependencies, not request-wide dependencies
3. define a per_request:bool, if true, reinstantiate the dependency for every request

eg.


def get_auth_service(
    settings,
    user_repo = Depends(get_user_repo),
    token_registry = Depends(get_token_registry),
    token_encrypt = Depends(get_encryp),
    producer = Depends(get_producer),

):
    ...


auth_service: AuthService = Depends(get_auth_service)


in lifespan of app:

async def lifespan(app: FastAPI):
    settings = get_settings()
    async with DependencyContainer(settings) as container:
        yield

in various places:

from src.app.dependencies import DependencyContainer, Dependency

auth_service = DependencyContainer.auth_service

class ServiceRegistry:
    _registry: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
"""


import typing as ty
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)

from src.domain.config import Settings, SettingsFactory


class Dependency[TDep: object]:
    _name: str

    def __init__(
        self,
        dependency: type[TDep],
        factory: SettingsFactory[TDep],
        reuse: bool = True,
    ):
        self.dependency = dependency
        self.factory = factory
        self.reuse = reuse
        self._name = ""

    def __set_name__(self, owner: type["ServiceRegistryBase"], name: str):
        if self._name == "":
            self._name = name
            return

        if self._name != name:
            raise RuntimeError(
                f"Dependency {self._name} is already defined for {owner.__name__}"
            )

    def __repr__(self):
        return f"<Dependency {self.dependency.__name__} reuse={self.reuse}>"

    def __get__[
        T: "ServiceRegistryBase"
    ](self, container: T | None, owner: type[T]) -> TDep | "Dependency[TDep]":
        if self.reuse is True and owner._registry.get(self.dependency, None):
            return owner._registry[self.dependency]

        registry = container or owner._singleton

        if registry is None:
            # raise RuntimeError("ServiceRegistry is not initialized")
            return self

        dep = self.factory(registry._settings)
        registry.register_service(dep)
        return dep


class ServiceRegistryBase[TService: ty.AsyncContextManager | ty.ContextManager]:
    _registry: dict[type[TService], TService] = dict()
    _dependencies: dict[type[TService], Dependency[TService]] = dict()

    _exit_stack: ty.ClassVar[AsyncExitStack] = AsyncExitStack()
    _singleton: ty.ClassVar[ty.Optional["ServiceRegistryBase"]] = None

    def __new__(cls, settings: Settings):
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
            return cls._singleton

        if cls._singleton._settings != settings:
            raise RuntimeError("ServiceRegistry is already initialized")
        return cls._singleton

    def __init__(self, settings: Settings):
        self._settings = settings

    def __init_subclass__(cls) -> None:
        for name, dep in cls.__dict__.items():
            if not isinstance(dep, Dependency):
                continue
            cls._dependencies[dep.dependency] = dep

    async def __aenter__(self):
        await self._exit_stack.__aenter__()

        for dep in self._dependencies.values():
            # TODO: maybe factory can also be context manager?
            service = dep.factory(self._settings)
            if isinstance(service, AbstractAsyncContextManager):
                await self._exit_stack.enter_async_context(service)  # type: ignore
            elif isinstance(service, AbstractContextManager):
                self._exit_stack.enter_context(service)

            self._registry[dep.dependency] = service
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
        self._registry.clear()

    def register_service(self, service: TService):
        self._registry[service.__class__] = service

        if isinstance(service, AbstractAsyncContextManager):
            self._exit_stack.push_async_exit(service)  # type: ignore
        elif isinstance(service, AbstractContextManager):
            self._exit_stack.push(service)
