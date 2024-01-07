import asyncio
import typing as ty
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    AsyncExitStack,
)

from src.domain.config import Settings, SettingsFactory
from src.domain.interface import LiveService

type ServiceLike = ty.AsyncContextManager | ty.ContextManager | LiveService


def categorize_service(service: type[ServiceLike]):
    for ser_type in ServiceLike.__value__.__args__:  # type: ignore
        if issubclass(service, ser_type):
            return ser_type
    return None


class InvalidServiceError(Exception):
    def __init__(self, dep: type[ServiceLike]):
        msg = f"Dependency {dep} is not a {ServiceLike}"
        super().__init__(msg)


class ServiceUninitializedError(Exception):
    def __init__(self, registry_cls: type["ServiceRegistryBase"]):
        msg = f"ServiceRegistry {registry_cls.__name__} is not initialized"
        super().__init__(msg)


class ServiceReinitializationError(Exception):
    def __init__(self):
        super().__init__("ServiceRegistry is already initialized")


# from fastapi.dependencies.utils import get_dependant


class Dependency[TDep: ServiceLike]:
    _name: str

    def __init__(
        self,
        dependency: type[TDep],
        factory: SettingsFactory[TDep] | None = None,
        reuse: bool = True,
    ):
        self.dependency = dependency
        if not (service_type := categorize_service(dependency)):
            raise InvalidServiceError(dep=dependency)

        self.factory = factory
        self.reuse = reuse
        self._name = ""
        self._service_type = service_type

    def __set_name__(self, registry_cls: type["ServiceRegistryBase"], name: str):
        if self._name == "":
            self._name = name
            return

        if self._name != name:
            raise RuntimeError(
                f"Dependency {self._name} is already defined for {registry_cls.__name__}"
            )

    def __repr__(self):
        return f"<Dependency {self.dependency.__name__} reuse={self.reuse}>"

    def __get__[
        T: "ServiceRegistryBase"
    ](self, registry: T | None, registry_cls: type[T]) -> TDep:
        if self.reuse is True and registry_cls._registry.get(self.dependency, None):
            return registry_cls._registry[self.dependency]

        registry = registry or registry_cls._singleton

        if registry is None:
            raise ServiceUninitializedError(registry_cls)

        dep = self.get_dependency(settings=registry._settings)
        registry.register_service(dep)
        return dep

    def get_dependency(self, settings: Settings) -> TDep:
        """
        TODO: maybe factory can also be context manager?
        """
        if self.factory is None:
            return self.dependency()

        service = self.factory(settings)
        return service


class ServiceRegistryBase[TService: ServiceLike]:
    _registry: dict[type[TService], TService] = dict()
    _dependencies: dict[type[TService], Dependency[TService]] = dict()

    _exit_stack: ty.ClassVar[AsyncExitStack] = AsyncExitStack()
    _singleton: ty.ClassVar[ty.Optional["ServiceRegistryBase"]] = None

    def __new__(cls, settings: Settings):
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
            return cls._singleton

        if cls._singleton._settings != settings:
            raise ServiceReinitializationError
        return cls._singleton

    def __init__(self, settings: Settings):
        self._settings = settings
        self.__lock = asyncio.Lock()

    def __init_subclass__(cls) -> None:
        for name, dep in cls.__dict__.items():
            if not isinstance(dep, Dependency):
                continue
            cls._dependencies[dep.dependency] = dep

    async def __aenter__(self) -> ty.Self:
        await self._exit_stack.__aenter__()

        for dep in self._dependencies.values():
            service = dep.get_dependency(settings=self._settings)

            if isinstance(service, AbstractAsyncContextManager):
                await self._exit_stack.enter_async_context(service)  # type: ignore
            elif isinstance(service, AbstractContextManager):
                self._exit_stack.enter_context(service)
            elif isinstance(service, LiveService):
                await self._exit_stack.enter_async_context(service.lifespan())

            self._registry[dep.dependency] = service
        return self

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
        self._registry.clear()

    def register_service(self, service: TService):
        self._registry[service.__class__] = service

        if isinstance(service, AbstractAsyncContextManager):
            self._exit_stack.push_async_exit(service)  # type: ignore
        elif isinstance(service, AbstractContextManager):
            self._exit_stack.push(service)


type Dep[TService: ServiceLike, TFactory: ty.Callable] = ty.Annotated[
    TService, Dependency[TService]
]


def solve_dependency(service: type):
    import inspect
    import types

    sub_deps = inspect.get_annotations(service.__init__)
    for dep_name, dep_annt in sub_deps.items():
        if not isinstance(dep_annt, types.GenericAlias):
            continue
        if not isinstance(dep_annt.__value__, ty._AnnotatedAlias):  # type: ignore
            continue

        annt_metas = dep_annt.__value__.__metadata__
        assert Dependency in annt_metas

        dep, faq = dep_annt.__args__
        return Dependency(dep, faq)
