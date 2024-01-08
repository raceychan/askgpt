"""
Custom types and helpers, do not import any non-builtin here.
"""
import typing as ty
from functools import lru_cache, update_wrapper

from src.adapters.cache import KeySpace as KeySpace


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


class TimeScale:
    "A more type-aware approach to time scale"
    Second = ty.NewType("Second", int)
    Minute = ty.NewType("Minute", int)
    Hour = ty.NewType("Hour", int)
    Day = ty.NewType("Day", int)
    Week = ty.NewType("Week", int)
