import inspect
import typing as ty
from dataclasses import dataclass, field

# from askgpt.app.auth.service import AuthService

"""
class DependencyTree:
    ...

async def create_user(user_id: str, user_name: str, dt: DependencyTree) -> None:
    await dt.auth_service.create_user(user_id, user_name)

@dt.node
def cache_factory() -> Cache:
    return RedisCache[str](redis=redis, keyspace=keyspace)
"""
# def is_subtitutable(node: DependencyNode, subtitude: type) -> bool:
#     return issubclass(subtitude, node.dependent)


from fastapi.dependencies.utils import get_typed_signature


@dataclass(kw_only=True)
class DependencyNode[T]:
    """
    name: name of the dependent, e.g cache_factory -> "cache_factory"
    dependent: the callable that this node represents, e.g cache_factory -> cache_factory, AuthService -> AuthService
    dependencies: the dependencies of the dependent, e.g cache_factory -> redis, keyspace
    """

    name: str
    dependent: ty.Callable[..., T] | type[T]
    default: T | None = None
    dependencies: list["DependencyNode[ty.Any]"] = field(default_factory=list)

    def build(self) -> T:
        if not self.dependencies:
            if self.default is not None:
                return self.default
            return self.dependent()

        args = {}
        for dep in self.dependencies:
            built_dep = dep.build()
            if built_dep is not None:
                args[dep.name] = built_dep
            elif dep.default is not None:
                args[dep.name] = dep.default

        return self.dependent(**args)

    @classmethod
    def from_signature[
        I
    ](cls, callable: ty.Callable[..., I] | type[I]) -> "DependencyNode[I]":
        if inspect.isclass(callable):
            signature = get_typed_signature(callable.__init__)
            name = callable.__name__
        else:
            signature = get_typed_signature(callable)
            name = callable.__name__

        node = DependencyNode(name=name, dependent=callable)

        params = tuple(signature.parameters.values())

        if inspect.isclass(callable) or inspect.ismethod(callable):
            params = params[1:]

        for param in params:
            dependency = process_param(param)
            if dependency:
                node.dependencies.append(dependency)
        return ty.cast("DependencyNode[I]", node)


def process_param(param: inspect.Parameter) -> DependencyNode[ty.Any] | None:
    annotation = param.annotation
    param_name = param.name

    # Handle default values
    if param.default != inspect.Parameter.empty:
        return DependencyNode(
            name=param_name, dependent=annotation, default=param.default
        )

    if inspect.isclass(annotation):
        return DependencyNode(name=param_name, dependent=annotation)
    elif hasattr(annotation, "__origin__"):  # For handling generic types
        origin = ty.get_origin(annotation)
        args = ty.get_args(annotation)
        node = DependencyNode(name=param_name, dependent=origin)
        for i, arg in enumerate(args):
            dependency = process_param(
                inspect.Parameter(
                    f"{param_name}_arg{i}",
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=arg,
                )
            )
            if dependency:
                node.dependencies.append(dependency)
        return node
    return None


def print_dependency_tree(node: DependencyNode[ty.Any], level: int = 0):
    indent = "  " * level
    print(f"{indent} {node.name=}, {node.dependent=}, {node.default=}")
    for dep in node.dependencies:
        print_dependency_tree(dep, level + 1)


class A:
    def __init__(self, a: int = 5):
        self.a = a


class B:
    def __init__(self, b: str = "b"):
        self.b = b


class C:
    def __init__(self, a: A, b: B, n: int = 1):
        self.a = a
        self.b = b
        self.n = n


# def c_factory(a: A, b: "B", n: int = 5) -> C:
#     return C(a, b, n)


if __name__ == "__main__":
    node = DependencyNode.from_signature(C)
    obj_c = node.build()
    assert obj_c.a.a == 5
    assert obj_c.b.b == "b"
    assert obj_c.n == 1
    print_dependency_tree(node)
