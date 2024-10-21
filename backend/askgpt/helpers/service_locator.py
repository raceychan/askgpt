import inspect
import types
import typing as ty
from contextlib import AsyncExitStack, asynccontextmanager
from weakref import WeakKeyDictionary

from askgpt.helpers.functions import attribute

"""
some might argue that service locator pattern is an anti-pattern,
but we improve it and remove many drawbacks the original version has
https://www.codeproject.com/Articles/5337102/Service-Locator-Pattern-in-Csharp
Disadvantages of this pattern(after our improvements) are:

- Implementing the service locator as a singleton can create scalability problems in highly concurrent environments.
- Testability problems might arise since all tests need to use the same global ServiceLocator (singleton).
- During unit testing, you need to mock both the ServiceLocator and the services it locates.

from martin fowler:
https://martinfowler.com/articles/injection.html#UsingAServiceLocator

The key difference is that with a Service Locator every user of a service has a dependency to the locator.
The locator can hide dependencies to other implementations, but you do need to see the locator.
So the decision between locator and injector depends on whether that dependency is a problem.
"""

"""
TODO: make a dependency tree, where root node is the app
           APP
        /       \
AuthService    GPTService

     /               \
UserRepository     SessionRepository
...
how can we achieve pytest.fixture?
reference:
pytest.fixtures.py -> FixtureManager
pytest.fixtures.py -> FixtureRequest.getfixturevalue

pytest.nodes.py -> Node
pytest.python.py -> PyCollector

API would be something like

@dependency_node
def settings():
    return Settings.from_file(sys.argv[1])

@dependency_node(reuse=False) # each call would create a new engine
def engine(settings: Settings):
    return AsyncDatabase(engine)

@dependency_node
def aiodb(engine: AsyncEngine):
    return AsyncDatabase(engine)

@dependency_node
def user_repository(aiodb: AsyncDatabase):
    return UserRepository(aiodb)
"""


@ty.runtime_checkable
class LiveService(ty.Protocol):
    @asynccontextmanager
    async def lifespan(self) -> ty.AsyncGenerator[ty.Self, ty.Any]: ...


@ty.runtime_checkable
class Closable(ty.Protocol):
    async def close(self) -> None: ...


type Resource = ty.AsyncContextManager[ty.Any] | ty.ContextManager[
    ty.Any
] | LiveService | Closable

type DepFactory[T] = ty.Callable[[ty.Any], T]


def solve_dependency(service: type):
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
    def __init__(self, registry_cls: type["DependencyRegistry[ty.Any]"]):
        msg = f"ServiceRegistry {registry_cls.__name__} is not initialized"
        super().__init__(msg)


class ServiceReinitializationError(Exception):
    def __init__(self):
        super().__init__("ServiceRegistry is already initialized")


class ResourceIntializationError(Exception):
    def __init__(self, resource: Resource, exc: Exception):
        msg = f"Failed to initialize {type(resource)}, \n {exc.__class__.__name__}:{str(exc)}"
        super().__init__(msg)


def resource_check(obj: ty.Any) -> bool:
    ResourceTypes = ty.get_args(Resource.__value__)  # type: ignore
    for tp in ResourceTypes:
        resource_type = ty.get_origin(tp) or tp
        if isinstance(obj, resource_type):
            return True
    return False


class ResourceManager:
    def __init__(self):
        self._stack = AsyncExitStack()
        self._resources: list[Resource] = []

    def register(self, resource: Resource):
        if not resource_check(resource):
            raise InvalidResourceError(resource)
        self._resources.append(resource)

    async def __aenter__(self):
        await self._stack.__aenter__()

        for resource in self._resources:
            try:
                if isinstance(resource, LiveService):
                    await self._stack.enter_async_context(resource.lifespan())
                elif isinstance(resource, Closable):
                    self._stack.push_async_callback(resource.close)
                elif isinstance(resource, ty.AsyncContextManager):
                    await self._stack.enter_async_context(resource)
                else:
                    self._stack.enter_context(resource)
            except Exception as e:
                raise ResourceIntializationError(resource, e) from e

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
        factory: DepFactory[TDep] | None = None,
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

    def __set_name__(self, registry_cls: type["DependencyRegistry[ty.Any]"], name: str):
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
        T: "DependencyRegistry[ty.Any]"
    ](self, registry: T | None, registry_cls: type[T]) -> TDep:
        if self._reuse is True and registry_cls.registry.get(self._dependency, None):
            return registry_cls.registry[self._dependency]

        registry = registry_cls.singleton

        dep = self.solve_dependency(settings=registry.settings)
        registry_cls.registry[self._dependency] = dep
        return dep

    def solve_dependency(self, settings: ty.Any) -> TDep:
        # TODO: add dependency graph, support contextmanager
        if self._factory is None:
            return self._dependency()

        service = self._factory(settings)
        return service

    def override_factory(self, factory: DepFactory[TDep]) -> None:
        self._factory = factory


class DependencyRegistry[Registee: ty.Any]:

    _registry: WeakKeyDictionary[type[Registee], Registee]
    _dependencies: WeakKeyDictionary[type[Registee], Dependency[Registee]]
    _singleton: ty.ClassVar["ty.Self | None"]

    def __init_subclass__(cls) -> None:
        cls._dependencies = WeakKeyDictionary()
        for _, dep in cls.__dict__.items():
            if isinstance(dep, Dependency):
                cls._dependencies[dep.dependency] = dep
        cls._singleton = None

    def __new__(cls, settings: ty.Any) -> ty.Self:
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
            cls._registry: WeakKeyDictionary[type[Registee], Registee] = (
                WeakKeyDictionary()
            )
            return cls._singleton

        if cls._singleton._settings is not settings:
            raise ServiceReinitializationError
        return cls._singleton

    def __init__(self, settings: ty.Any) -> None:
        self._settings = settings

    @attribute
    def settings(self) -> ty.Any:
        if self._singleton is None:
            raise RegistryUninitializedError(self.__class__)
        return self._singleton._settings

    @attribute
    def singleton(self) -> ty.Self:
        if self._singleton is None:
            raise RegistryUninitializedError(self.__class__)
        return self._singleton

    @attribute
    def registry(self) -> WeakKeyDictionary[type[Registee], Registee]:
        try:
            return self._registry
        except AttributeError:
            raise RegistryUninitializedError(self.__class__)

    @classmethod
    def override(cls, registee: type[Registee], factory: DepFactory[Registee]) -> None:
        """
        for dep in self._dependencies:
            mro = dep._dependency.__origin__.__mro__
        """
        cls._dependencies[registee].override_factory(factory)


class ResourceRegistry[Registee: Resource](DependencyRegistry[Registee]):
    "Provide extra lifetime management based upon registrybase"
    _registry: WeakKeyDictionary[type[Registee], Registee]
    _dependencies: WeakKeyDictionary[type[Registee], Dependency[Registee]]
    _singleton: ty.ClassVar["ty.Self | None"]

    def __init__(self, settings: ty.Any):
        super().__init__(settings)
        self._resource_manager = ResourceManager()

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
    def dependencies(self) -> WeakKeyDictionary[type[Registee], Dependency[Registee]]:
        return self._dependencies

    def register_context(self, resource: Registee) -> None:
        self._resource_manager.register(resource)


class InfraLocator(ResourceRegistry[ty.Any]): ...
