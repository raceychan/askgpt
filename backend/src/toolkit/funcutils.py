import typing as ty
from functools import lru_cache
from functools import partial as partial
from functools import update_wrapper

AnyCallable = ty.Callable[..., ty.Any]


@ty.overload
def simplecache(max_size: int, strict: bool) -> AnyCallable: ...


@ty.overload
def simplecache[**P, R](max_size: ty.Callable[P, R]) -> ty.Callable[P, R]: ...


def simplecache(max_size: int | AnyCallable = 1, strict: bool = False):
    _max_size = 1 if callable(max_size) else max_size

    def _simplecache[**P, R](user_func: ty.Callable[P, R]) -> ty.Callable[P, R]:
        sentinel = object()
        cache: dict[int, ty.Any] = {}

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key_val = hash(tuple(args) + tuple(kwargs.values()))
            if (cached_res := cache.get(key_val, sentinel)) is not sentinel:
                return cached_res
            if len(cache) >= _max_size:
                if strict:
                    raise RuntimeError("Cache is full")
                cache.popitem()
            res = user_func(*args, **kwargs)
            cache[key_val] = res
            return res

        return wrapper

    if callable(max_size):
        return _simplecache(max_size)
    else:
        return _simplecache


class hashabledict[TKey, TVal](dict[TKey, TVal]):
    def __hash__(self):  # type: ignore
        return hash(frozenset(self))


FREEZER_MAP: dict[type, ty.Callable[[ty.Any], ty.Any]] = {
    dict: hashabledict,
    set: frozenset,
    list: tuple,
}


def freeze(
    obj: object, convert_map: dict[type, ty.Callable[[ty.Any], ty.Any]] | None = None
) -> object:
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
    convert_map: dict[type, AnyCallable] | None = None,
    maxsize: int = 1,
) -> ty.Callable[P, R]:
    """\
    ### LRU-cache with type conversion \n This converts mutable arguments to immutable, so that method with mutable arguments can be cached \
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

    @ty.overload
    def __init__(
        self,
        fget: ty.Callable[[TOwner], TField] | None = None,
        fset: ty.Callable[[TOwner, TField], None] | None = None,
    ) -> None: ...

    @ty.overload
    def __init__(
        self,
        fget: ty.Callable[[type[TOwner]], TField] | None = None,
        fset: ty.Callable[[type[TOwner], TField], None] | None = None,
    ) -> None: ...

    def __init__(
        self,
        fget: ty.Callable | None = None,
        fset: ty.Callable | None = None,
    ):
        self.fget = fget
        self.fset = fset
        self._attrname: str = ""
        self.__doc__ = fget.__doc__ if fget else None

    def __set_name__(self, owner_type: type[TOwner], name: str) -> None:
        if self._attrname == "":
            self._attrname = name
            return

        if name != self._attrname:
            raise TypeError("cannot assign the same attribute name twice")

    def __get__(self, owner_object, owner_type: type[TOwner]) -> TField:
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
