"""
1. API design:
class ServiceRegistry(ServiceRegistryBase):
    gpt_service: Dependency[GPTService, get_gpt_service]
    or 
    gpt_service = dependency(GPTService, get_gpt_service)

async with ServiceRegistry(settings) as registry:
    yield registry

gpt_service = registry.gpt_service()
registry.gpt_service.override_factory(get_gpt_service)
2. nested dependency detech
create a dependency graph using stacks
[ServiceRegistry, GPTService, GPTSystem, QueueBox, Cache]
each of them can be a dependency themself, thus we need to extract the dependency from the class
[
 ServiceRegistry deps: [dep1, dep2, dep3]   
]

"""
import types
import typing as ty
from contextlib import AsyncExitStack

from src.domain.config import Settings, SettingsFactory
from src.domain.interface import Closable, LiveService
from src.toolkit.funcutils import attribute

type Resource = ty.AsyncContextManager[ty.Any] | ty.ContextManager[
    ty.Any
] | LiveService | Closable
# type Dep[TService: Resource, TFactory: ty.Callable] = ty.Annotated[
#     TService, "Dependency[TService]"
# ]


def solve_dependency(service: type):
    import inspect
    import types

    sub_deps = inspect.get_annotations(service.__init__)
    for _, dep_annt in sub_deps.items():
        if not isinstance(dep_annt, types.GenericAlias):
            continue
        if not isinstance(dep_annt.__value__, ty._AnnotatedAlias):  # type: ignore
            continue

        annt_metas = dep_annt.__value__.__metadata__
        assert Dependency in annt_metas

        dep, faq = dep_annt.__args__
        return Dependency(dep, faq)


class InvalidResourceError(Exception):
    def __init__(self, dep: type[Resource] | Resource):
        msg = f"Dependency {dep} is not a {Resource}"
        super().__init__(msg)


class RegistryUninitializedError(Exception):
    def __init__(self, registry_cls: type["RegistryBase[ty.Any]"]):
        msg = f"ServiceRegistry {registry_cls.__name__} is not initialized"
        super().__init__(msg)


class ServiceReinitializationError(Exception):
    def __init__(self):
        super().__init__("ServiceRegistry is already initialized")


def resource_check(obj: ty.Any) -> bool:
    ResourceTypes = ty.get_args(Resource.__value__)  # type: ignore
    for tp in ResourceTypes:
        resource_type = ty.get_origin(tp) or tp
        if isinstance(obj, resource_type):
            return True
    return False


class ResourceManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._stack = AsyncExitStack()
        self._resources: list[Resource] = []

    def register(self, resource: Resource):
        if not resource_check(resource):
            raise InvalidResourceError(resource)
        self._resources.append(resource)

    async def __aenter__(self):
        await self._stack.__aenter__()

        for resource in self._resources:
            if isinstance(resource, LiveService):
                await self._stack.enter_async_context(resource.lifespan())
            elif isinstance(resource, Closable):
                self._stack.push_async_callback(resource.close)
            elif isinstance(resource, ty.AsyncContextManager):
                await self._stack.enter_async_context(resource)
            else:
                self._stack.enter_context(resource)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ):
        await self._stack.__aexit__(exc_type, exc_val, exc_tb)
        self._resources.clear()


class Dependency[TDep: ty.Any]:
    _name: str

    def __init__(
        self,
        dependency: type[TDep],
        factory: SettingsFactory[TDep] | None = None,
        reuse: bool = True,
    ):
        self._dependency = dependency
        self._factory = factory
        self._reuse = reuse
        self._name = ""

    @property
    def dependency(self) -> type[TDep]:
        return self._dependency

    @property
    def factory(self):
        return self._factory

    def __set_name__(self, registry_cls: type["RegistryBase[ty.Any]"], name: str):
        if self._name == "":
            self._name = name
            return

        if self._name != name:
            raise RuntimeError(
                f"Dependency {self._name} is already defined for {registry_cls.__name__}"
            )

    def __repr__(self):
        return f"<Dependency {self._dependency.__name__} reuse={self._reuse}>"

    def __get__[
        T: "RegistryBase[ty.Any]"
    ](self, registry: T | None, registry_cls: type[T]) -> TDep:
        if self._reuse is True and registry_cls.registry.get(self._dependency, None):
            return registry_cls.registry[self._dependency]

        registry = registry_cls.singleton

        dep = self.solve_dependency(settings=registry.settings)
        registry_cls.registry[self._dependency] = dep
        return dep

    def solve_dependency(self, settings: Settings) -> TDep:
        # TODO: add dependency graph, support contextmanager
        if self._factory is None:
            return self._dependency()

        service = self._factory(settings)
        return service

    def override_factory(self, factory: ty.Callable[[ty.Any], TDep]) -> None:
        self._factory = factory


class RegistryBase[Registee: ty.Any]:
    _dependencies: dict[type[Registee], Dependency[Registee]]
    _singleton: ty.ClassVar["ty.Self | None"]

    def __init_subclass__(cls) -> None:
        cls._dependencies: dict[type[Registee], Dependency[Registee]] = dict()
        for _, dep in cls.__dict__.items():
            if not isinstance(dep, Dependency):
                continue
            cls._dependencies[dep.dependency] = dep  # type: ignore

        cls._singleton = None

    def __new__(cls, settings: Settings) -> ty.Self:
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
            cls._registry: dict[type[Registee], Registee] = dict()
            return cls._singleton

        if cls._singleton._settings != settings:
            raise ServiceReinitializationError
        return cls._singleton

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @attribute
    def settings(self) -> Settings:
        if self._singleton is None:
            raise RegistryUninitializedError(self.__class__)
        return self._singleton._settings

    @attribute
    def singleton(self) -> ty.Self:
        if self._singleton is None:
            raise RegistryUninitializedError(self.__class__)
        return self._singleton

    @attribute
    def registry(self) -> dict[type[Registee], Registee]:
        return self._registry

    def override(
        self, registee: type[Registee], factory: ty.Callable[[ty.Any], Registee]
    ) -> None:
        self._dependencies[registee].override_factory(factory)


class ResourceRegistry[Registee: Resource](RegistryBase[Registee]):
    _registry: dict[type[Registee], Registee]
    _dependencies: dict[type[Registee], Dependency[Registee]]
    _singleton: ty.ClassVar["ty.Self | None"]

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._resource_manager = ResourceManager(settings)

    async def __aenter__(self) -> ty.Self:
        for dep in self._dependencies.values():
            service = dep.solve_dependency(settings=self._settings)
            self._resource_manager.register(service)
        await self._resource_manager.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: type[Exception], exc_val: Exception, exc_tb: types.TracebackType
    ) -> None:
        await self._resource_manager.__aexit__(exc_type, exc_val, exc_tb)

    @attribute
    def resource_manager(self) -> ResourceManager:
        return self._resource_manager

    @attribute
    def dependencies(self):
        return self._dependencies

    def register(self, service: Registee) -> None:
        self._resource_manager.register(service)


class ServiceRegistryBase[TService: object](RegistryBase[TService]):
    ...


class InfraRegistryBase(ResourceRegistry[ty.Any]):
    ...
