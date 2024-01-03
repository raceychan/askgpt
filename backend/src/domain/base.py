"""
Custom types and helpers, do not import any non-builtin here.
"""
import typing as ty
from functools import lru_cache, update_wrapper


class _NotGiven:
    ...


NOT_GIVEN = _NotGiven()

# use as default value for str, singleton
EMPTY_STR: ty.Annotated[str, "EMPTY_STR"] = ""

# Where None does not mean default value, but a valid value to be set
type Nullable[T] = T | _NotGiven | None


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

        update_wrapper(frozenfactory, factory)
        return frozenfactory

    return decorated(factory) if factory else decorated


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
        self._attrname: str = EMPTY_STR
        self.__doc__ = fget.__doc__ if fget else None

    def __set_name__(self, owner_type: type[TOwner], name: str) -> None:
        if self._attrname is EMPTY_STR:
            self._attrname = name
            return

        if name != self._attrname:
            raise TypeError("cannot assign the same attribute name twice")

    def __get__(self, owner_object: TOwner | None, owner_type: type[TOwner]) -> ty.Any:
        if not self.fget:
            raise AttributeError("unreadable attribute")

        owner = owner_object or owner_type
        return self.fget(owner)

    def __set__(self, instance: TOwner, value: TField) -> None:
        if not self.fset:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)

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
        # fun fact: this is slower than str.split
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

    def __truediv__(self, other: ty.Union[str, "KeySpace"]) -> "KeySpace":
        if isinstance(other, self.__class__):
            return KeySpace(self.key + ":" + other.key)

        if isinstance(other, str):
            return KeySpace(self.key + ":" + other)

        raise TypeError

    @property
    def parent(self):
        return KeySpace(self.key[: self.key.rfind(":")])

    @property
    def base(self):
        return KeySpace(self.key[: self.key.find(":")])

    def generate_for_cls(self, cls: type) -> "KeySpace":
        mod = cls.__module__
        return self(mod + ":" + cls.__name__)
