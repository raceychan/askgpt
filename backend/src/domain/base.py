"""
Custom types and helpers, do not import any non-builtin here.
"""
import typing as ty
from functools import lru_cache


class _NotGiven:
    ...


NOT_GIVEN = _NotGiven()

# use as default value for str, singleton
EMPTY_STR: ty.Annotated[str, "EMPTY_STR"] = ""

# Where None does not mean default value, but a valid value to be set
type Nullable[T] = T | _NotGiven | None


class attribute[TOwner: ty.Any, TField: ty.Any]:
    """
    like property, but works for both class and instance.
    """

    def __init__(
        self,
        fget: ty.Callable[[TOwner | type[TOwner]], TField] | None = None,
        fset: ty.Callable[[TOwner | type[TOwner], TField], None] | None = None,
    ):
        self.fget = fget
        self.fset = fset

    def __get__(self, instance: TOwner | None, owner: type[TOwner]) -> ty.Any:
        if self.fget:
            return self.fget(instance) if instance else self.fget(owner)
        raise AttributeError("unreadable attribute")

    def setter(
        self, fset: ty.Callable[[TOwner | type[TOwner], TField], None]
    ) -> ty.Self:
        return type(self)(self.fget, fset)


class KeySpace(ty.NamedTuple):  # use namedtuple for memory efficiency
    """Organize key to create redis key namespace \n\
    >>> KeySpace("base")("new").key
    'base:new'
    """

    key: str = ""

    def __iter__(self):
        # this is slower than str.split, but more fun
        left, right, end = 0, 1, len(self.key)

        while right < end:
            if self.key[right] == ":":
                yield self.key[left:right]
                left = right + 1
            right += 1
        yield self.key[left:right]

    def __call__(self, next_part: str) -> "KeySpace":
        if not self.key:
            return KeySpace(next_part)
        return KeySpace(f"{self.key}:{next_part}")

    @property
    def parent(self):
        return KeySpace(self.key[: self.key.rfind(":")])

    @property
    def base(self):
        return KeySpace(self.key[: self.key.find(":")])

    def generate_for_cls(self, cls: type) -> "KeySpace":
        mod = cls.__module__
        return self(mod + ":" + cls.__name__)


class hashabledict[TKey, TVal](dict[TKey, TVal]):
    def __hash__(self):
        return hash(frozenset(self))


FREEZER_MAP: dict[type, ty.Callable] = {
    dict: hashabledict,
    set: frozenset,
    list: tuple,
}


def freeze(obj: object, convert_map: dict[type, ty.Callable] | None = None) -> object:
    mapper = {**FREEZER_MAP, **(convert_map or {})}
    frozen_type = mapper.get(type(obj), None)
    if frozen_type is None:
        return obj
    return frozen_type(obj)


def freezelru[
    **P, R
](
    factory: ty.Callable[P, R] | None = None,
    *,
    convert_map: dict[type, ty.Callable] | None = None,
    maxsize: int = 1,
) -> ty.Callable[P, R]:
    """\
    ### LRU-cache with type conversion \n This converts mutable arguments to immutable. \
    Combine this and factory method forms flyweight pattern\
    """

    def decorated(factory: ty.Callable[P, R]) -> ty.Callable[P, R]:
        cachedfactory = lru_cache(maxsize=maxsize)(factory)

        def frozenfactory(*args: P.args, **kwargs: P.kwargs) -> R:
            fzargs = tuple(freeze(arg, convert_map) for arg in args)
            fzkwargs = {k: freeze(v, convert_map) for k, v in kwargs.items()}
            return cachedfactory(*fzargs, **fzkwargs)

        return frozenfactory

    return decorated if factory is None else decorated(factory)
