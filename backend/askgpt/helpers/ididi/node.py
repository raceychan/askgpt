import abc
import inspect
import types
import typing as ty
from dataclasses import dataclass, field
from inspect import Parameter

from .errors import (
    ABCWithoutImplementationError,
    CircularDependencyDetectedError,
    ForwardReferenceNotFoundError,
    GenericDependencyNotSupportedError,
    MissingAnnotationError,
    NotSupportedError,
    ProtocolFacotryNotProvidedError,
    UnsolvableDependencyError,
)
from .utils.param_utils import NULL, Nullable
from .utils.typing_utils import (
    eval_type,
    get_full_typed_signature,
    get_typed_annotation,
    is_builtin_type,
)

EMPTY_SIGNATURE = inspect.Signature()


def is_class_or_method(obj: ty.Any) -> bool:
    return isinstance(obj, (type, types.MethodType))


def is_class(obj: type | ty.Callable[..., ty.Any]) -> bool:
    origin = ty.get_origin(obj) or obj
    is_type = isinstance(origin, type)
    is_generic_alias = isinstance(obj, types.GenericAlias)
    return is_type or is_generic_alias


def is_class_with_empty_init(cls: type) -> bool:
    is_undefined_init = cls.__init__ is object.__init__
    is_protocol = type(cls) is ty._ProtocolMeta  # type: ignore
    return is_undefined_init or is_protocol


"""
TODO: search in global for factory,
we might search for prefix '_di_'
we can have _di_service_factory in the global namespace
def search_factory[
    I
](dependent: type[I], globalvars: dict[str, ty.Any] | None = None) -> (
    ty.Callable[..., I] | None
):
    raise NotSupportedError("searching to be implemented")
"""


def process_param[
    I
](
    *,
    dependent: type[I],
    param: inspect.Parameter,
    globalns: dict[str, ty.Any],
) -> "DependentNode[ty.Any]":
    """
    Process a parameter to create a dependency node.
    Handles forward references, builtin types, classes, and generic types.
    """
    param_name = param.name
    default = param.default if param.default != inspect.Parameter.empty else NULL

    annotation = get_typed_annotation(param.annotation, globalns)

    if hasattr(annotation, "__origin__"):
        annotation = ty.get_origin(annotation)

    if annotation is inspect.Parameter.empty:
        if param.kind in (Parameter.VAR_POSITIONAL, Parameter.KEYWORD_ONLY):
            raise NotSupportedError(f"Unsupported parameter kind: {param.kind}")
        raise MissingAnnotationError(dependent, param_name)

    if isinstance(annotation, ty.TypeVar):
        raise GenericDependencyNotSupportedError(annotation)

    # Handle builtin types
    if is_builtin_type(annotation):
        return DependentNode(
            dependent=Dependent(annotation),
            factory=annotation,
            default=default,
        )
    elif isinstance(annotation, type):
        return DependentNode.from_node(annotation)
    else:
        raise NotSupportedError(f"Unsupported annotation type: {annotation}")


@dataclass(frozen=True, slots=True)
class AbstractDependent[T]:
    """Base class for all dependent types."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__name__})"

    @property
    def __name__(self) -> str:
        """Return the name of the dependent type."""
        raise NotImplementedError

    def resolve(self) -> type[T]:
        """Resolve to concrete type."""
        raise NotImplementedError

    @property
    def dependent_type(self) -> type[T]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Dependent[T](AbstractDependent[T]):
    """Represents a concrete (non-forward-reference) dependent type."""

    _dependent_type: type[T]

    @property
    def __name__(self) -> str:
        return self._dependent_type.__name__

    @property
    def dependent_type(self) -> type[T]:
        return self._dependent_type

    def resolve(self) -> type[T]:
        return self._dependent_type

    def __hash__(self) -> int:
        return hash(self._dependent_type)


@dataclass(frozen=True, slots=True)
class ForwardDependent(AbstractDependent[ty.Any]):
    """A placeholder for a dependent type that hasn't been resolved yet."""

    forward_ref: ty.ForwardRef
    globalns: dict[str, ty.Any] = field(repr=False)

    def resolve(self) -> type:
        try:
            return eval_type(self.forward_ref, self.globalns, self.globalns)
        except NameError as e:
            raise ForwardReferenceNotFoundError(self.forward_ref) from e

    def __hash__(self) -> int:
        return hash(self.forward_ref.__forward_arg__)


"""
class LazyDependent(AbstractDependent[ty.Any]):
    def __getattr__(self, name: str) -> ty.Any:
        '''
        dynamically build the dependent type on the fly
        '''

    def resolve(self) -> ty.Self:
        return self
"""


@dataclass(kw_only=True, slots=True, frozen=True)
class DependencyParam:
    """Represents a parameter and its corresponding dependency node.

    This class encapsulates the relationship between a parameter and its
    dependency node, making the one-to-one relationship explicit.
    """

    name: str
    param: Parameter
    is_builtin: bool
    dependency: "DependentNode[ty.Any]"
    # is_actualized: bool

    @property
    def dependent_type(self) -> type[ty.Any]:
        return self.dependency.dependent_type

    def build(self, **kwargs: ty.Any) -> ty.Any:
        """Build the dependency if needed, handling defaults and overrides."""
        if self.param.name in kwargs:
            return kwargs[self.param.name]

        if self.param.default != Parameter.empty:
            return self.param.default

        if self.param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            return {}  # Skip *args and **kwargs if not provided

        return self.dependency.build()

    @classmethod
    def from_param[
        I
    ](
        cls, dependent: type[I], param: inspect.Parameter, globalns: dict[str, ty.Any]
    ) -> "DependencyParam":
        if isinstance(param.annotation, ty.ForwardRef):
            lazy_dep = ForwardDependent(param.annotation, globalns)
            dependency = DependentNode(
                dependent=lazy_dep,
                factory=lambda: None,
            )
            return cls(
                name=param.name, param=param, dependency=dependency, is_builtin=False
            )
        else:
            dependency = process_param(
                dependent=dependent,
                param=param,
                globalns=globalns,
            )
            return cls(
                name=param.name,
                param=param,
                dependency=dependency,
                is_builtin=is_builtin_type(dependency.dependent_type),
            )


@dataclass(kw_only=True, slots=True)
class DependentNode[T]:
    """
    A DAG node that represents a dependency

    Examples:
    -----
    ```python
    @dag.node
    class AuthService:
        def __init__(self, redis: Redis, keyspace: str):
            pass
    ```

    in this case:
    - dependent: the dependent type that this node represents, e.g AuthService
    - factory: the factory function that creates the dependent, e.g AuthService.__init__, auth_service_factory
    - dependencies: the dependencies of the dependent, e.g redis: Redis, keyspace: str
    """

    dependent: AbstractDependent[T]
    default: Nullable[T] = NULL
    factory: ty.Callable[..., T]
    dependency_params: list[DependencyParam] = field(default_factory=list, repr=False)

    def __hash__(self) -> int:
        return hash(self.dependent)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dependent.__name__})"

    @property
    def dependent_type(self) -> type[T]:
        return self.dependent.dependent_type

    @property
    def signature(self) -> inspect.Signature:
        """Reconstruct signature from dependency_params"""
        if not self.dependency_params:
            return EMPTY_SIGNATURE
        parameters = [dep.param for dep in self.dependency_params]
        return inspect.Signature(
            parameters=parameters, return_annotation=self.dependent
        )

    def resolve_forward_dependency(self, dep: ForwardDependent) -> type:
        """
        Resolve a forward dependency and check for circular dependencies.
        Returns the resolved type and its node.
        """

        resolved_type = dep.resolve()

        # Check for circular dependencies
        sub_params = get_full_typed_signature(resolved_type).parameters.values()
        for sub_param in sub_params:
            if sub_param.annotation is self.dependent.dependent_type:
                raise CircularDependencyDetectedError(
                    [self.dependent.dependent_type, resolved_type]
                )

        return resolved_type

    def resolve_forward_dependent_nodes(
        self,
    ) -> ty.Generator["DependentNode[ty.Any]", None, None]:
        """
        Update all forward dependency params to their resolved types.
        """
        for index, dep_param in enumerate(self.dependency_params):
            param = dep_param.param
            dep = dep_param.dependency.dependent

            if dep_param.is_builtin:
                continue

            if not isinstance(dep, ForwardDependent):
                continue

            resolved_type = self.resolve_forward_dependency(dep)
            resolved_node = DependentNode.from_node(resolved_type)
            new_dep_param = DependencyParam(
                name=param.name,
                param=param,
                dependency=resolved_node,
                is_builtin=False,
            )
            self.dependency_params[index] = new_dep_param
            yield resolved_node

    def build_type_without_dependencies(self) -> T:
        """
        This is mostly for types that can't be directly constrctured,
        e.g abc.ABC, protocols, builtin types that can't be instantiated without arguments.
        """
        if isinstance(self.factory, type):
            if is_builtin_type(self.factory):
                raise UnsolvableDependencyError(self.dependent.__name__, self.factory)

            if getattr(self.factory, "_is_protocol", False):
                raise ProtocolFacotryNotProvidedError(self.factory)

            if issubclass(self.factory, abc.ABC):
                if abstract_methods := self.factory.__abstractmethods__:
                    raise ABCWithoutImplementationError(self.factory, abstract_methods)
                return ty.cast(ty.Callable[..., T], self.factory)()

            return ty.cast(type[T], self.factory)()

        try:
            return self.factory()
        except Exception as e:
            raise UnsolvableDependencyError(
                str(self.dependent), type(self.factory)
            ) from e

    def build(self, *args: ty.Any, **kwargs: ty.Any) -> T:
        """
        Build the dependent, resolving dependencies and applying defaults.
        kwargs override any dependencies or defaults.
        """
        if not self.dependency_params:
            return self.build_type_without_dependencies()

        bound_args = self.signature.bind_partial()

        # Build all dependencies using DependencyParam
        for dep_param in self.dependency_params:
            value = dep_param.build(*args, **kwargs)
            if value is not None:  # Skip None values from *args/**kwargs
                bound_args.arguments[dep_param.param.name] = value

        bound_args.apply_defaults()
        return self.factory(*bound_args.args, **bound_args.kwargs)

    @classmethod
    def _create_node[
        N
    ](
        cls,
        *,
        dependent: type[N],
        factory: ty.Callable[..., N],
        signature: inspect.Signature,
    ) -> "DependentNode[N]":
        """Create a new dependency node with the specified type."""

        # TODO: we need to make errors happen within this function much more deatiled,
        # so that user can see right away what is wrong without having to trace back.

        params = tuple(signature.parameters.values())
        globalns = getattr(dependent.__init__, "__globals__", {})

        if is_class_or_method(factory):
            # Skip 'self' parameter
            params = params[1:]

        dependency_params = list(
            DependencyParam.from_param(dependent, param, globalns) for param in params
        )

        node = DependentNode(
            dependent=Dependent(dependent),
            factory=factory,
            dependency_params=dependency_params,
        )
        return node

    @classmethod
    def _from_factory[I](cls, factory: ty.Callable[..., I]) -> "DependentNode[I]":

        signature = get_full_typed_signature(factory)
        if signature.return_annotation is inspect.Signature.empty:
            raise ValueError("Factory must have a return type")
        dependent = ty.cast(type[I], signature.return_annotation)

        return cls._create_node(
            dependent=dependent, factory=factory, signature=signature
        )

    @classmethod
    def _from_class[I](cls, dependent: type[I]) -> "DependentNode[I]":
        if hasattr(dependent, "__origin__"):
            if res := ty.get_origin(dependent):
                dependent = res

        if is_class_with_empty_init(dependent):
            return cls._create_node(
                dependent=dependent,
                factory=ty.cast(ty.Callable[..., I], dependent),
                signature=EMPTY_SIGNATURE,
            )
        signature = get_full_typed_signature(dependent.__init__)
        signature = signature.replace(return_annotation=dependent)
        return cls._create_node(
            dependent=dependent, factory=dependent, signature=signature
        )

    @classmethod
    def from_node[I](cls, node: type[I] | ty.Callable[..., I]) -> "DependentNode[I]":
        if is_class(node):
            return cls._from_class(ty.cast(type[I], node))
        elif callable(node):
            return cls._from_factory(node)
        # else:
        #     raise NotSupportedError(f"Unsupported node type: {type(node)}")
