import typing as ty
from functools import lru_cache, update_wrapper

AnyCallable = ty.Callable[..., ty.Any]


class _Missing: ...


MISSING = _Missing()


class SimpleCacheFullError(Exception): ...


@ty.overload
def simplecache(max_size: int = 1, *, size_check: bool = False) -> AnyCallable: ...


@ty.overload
def simplecache[**P, R](max_size: ty.Callable[P, R]) -> ty.Callable[P, R]: ...


def simplecache(max_size: int | AnyCallable = 1, *, size_check: bool = False):
    """
    a simple cache that utilizes a dict instead of a double-linked list for caching

    Args:
        max_size : max number of result cached for the decorated function
        size_check: wether raise error when number of chaced results reach max_szie
    """
    _max_size = 1 if callable(max_size) else max_size

    def _simplecache[**P, R](user_func: ty.Callable[P, R]) -> ty.Callable[P, R]:
        cache: dict[int, R] = {}

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key_val = hash(tuple(args) + tuple(kwargs.values()))
            try:
                cached_res = cache[key_val]
            except KeyError:
                if len(cache) >= _max_size:
                    if size_check:
                        raise RuntimeError("Cache is full")
                    (k__ := next(iter(cache)), cache.pop(k__))  # type: ignore
                cache[key_val] = cached_res = user_func(*args, **kwargs)

            return cached_res

        return wrapper

    return _simplecache(max_size) if callable(max_size) else _simplecache


class hashabledict[TKey, TVal](dict[TKey, TVal]):
    def __hash__(self) -> int:
        return hash(frozenset(self))


FREEZER_MAP: dict[type, ty.Callable[[ty.Any], ty.Any]] = {
    dict: hashabledict,
    set: frozenset,
    list: tuple,
}


class UnhashableError(Exception): ...


def freeze(
    obj: object, convert_map: dict[type, ty.Callable[[ty.Any], ty.Any]] | None = None
) -> object:
    mapper = {**FREEZER_MAP, **(convert_map or {})}
    frozen_type = mapper.get(type(obj), None)

    if frozen_type is None:
        try:
            hash(obj)
        except TypeError as te:  # not hashable exception
            raise UnhashableError from te
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

    return decorated(factory) if factory else decorated  # type: ignore


type ObjGet[TOwner, TField] = ty.Callable[[TOwner], TField]
type ObjSet[TOwner, TField] = ty.Callable[[TOwner, TField], None]
type ClsGet[TOwner, TField] = ty.Callable[[type[TOwner]], TField]
type ClsSet[TOwner, TField] = ty.Callable[[type[TOwner], TField], None]


class attribute[TOwner, TField]:
    """
    like property, but works for both class and instance.
    """

    @ty.overload
    def __init__(
        self,
        fget: ObjGet[TOwner, TField],
        fset: ObjSet[TOwner, TField] | None = None,
    ) -> None: ...

    @ty.overload
    def __init__(
        self,
        fget: ClsGet[TOwner, TField] | None = None,
        fset: ClsSet[TOwner, TField] | None = None,
    ) -> None: ...

    def __init__(
        self,
        fget: ObjGet[TOwner, TField] | ClsGet[TOwner, TField] | None = None,
        fset: ObjSet[TOwner, TField] | ClsSet[TOwner, TField] | None = None,
    ):
        "__init__ will be executed before other descriptor mtehods"
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

    @ty.overload
    def __get__(self, owner_obj: TOwner, owner_type: type[TOwner]) -> TField: ...

    @ty.overload
    def __get__(
        self, owner_obj: ty.Literal[None], owner_type: type[TOwner]
    ) -> TField: ...

    def __get__(self, owner_obj: TOwner | None, owner_type: type[TOwner]) -> TField:
        if not self.fget:
            raise AttributeError("unreadable attribute")

        if owner_obj is None:
            self.fget = ty.cast(ClsGet[TOwner, TField], self.fget)
            return self.fget(owner_type)
        self.fget = ty.cast(ObjGet[TOwner, TField], self.fget)
        return self.fget(owner_obj)

    def __set__(self, owner_obj: TOwner, value: TField) -> None:
        """
        BUG?
        assigning value to attribute in a class won't trigger attribute.__set__"
        T.name = 5 # won't trigger name.__set__
        """
        raise NotImplementedError
        if not self.fset:
            raise AttributeError("can't set attribute")
        self.fset(owner_obj, value)

    def setter(
        self, fset: ty.Callable[[TOwner | type[TOwner], TField], None]
    ) -> ty.Self:
        return type(self)(self.fget, fset)


class cached_attribute[TOwner, TField](attribute[TOwner, TField]):
    """
    Cached version of attribute that stores the value after the first access.
    """

    def __get__(
        self, owner_object: TOwner | ty.Literal[None], owner_type: type[TOwner]
    ) -> TField:
        if owner_object is None:
            self.fget = ty.cast(ClsGet[TOwner, TField], self.fget)
            if not hasattr(owner_type, self._attrname):
                value = self.fget(owner_type)
                setattr(owner_type, self._attrname, value)
            return getattr(owner_type, self._attrname)
        else:
            self.fget = ty.cast(ObjGet[TOwner, TField], self.fget)
            if not hasattr(owner_object, self._attrname):
                value = self.fget(owner_object)
                setattr(owner_object, self._attrname, value)
            return getattr(owner_object, self._attrname)

    def __set__(self, instance: TOwner, value: TField) -> None:
        raise NotImplementedError
        if not self.fset:
            raise AttributeError("can't set attribute")
        self.fset(instance, value)
        setattr(instance, self._attrname, value)  # Cache the value


class ClassAttr[AttrType]:
    """
    Like the opposite of 'property',
    where this returns class attribute only if accssed via class
    and return itself otherwise.

    class Test:
        name: ClassAttr[str] = ClassAttr(lambda x: x.__name__.lower())

    assert Test.name == "test"
    assert isinstance(Test().name, ClassAttr)
    """

    def __init__(
        self,
        name_or_getter: str | ty.Callable[[type], AttrType],
        *,
        default: AttrType | _Missing = MISSING,
    ):
        self._name_or_getter = name_or_getter
        self._default = default

    def __set_name__(self, owner_type: type, name: str):
        self._set_name = name

    @ty.overload
    def __get__(self, owner_obj: None, owner_type: type[ty.Any]) -> AttrType: ...

    @ty.overload
    def __get__[
        T
    ](self, owner_obj: T, owner_type: type[T] | None = None) -> ty.Self: ...

    def __get__[
        T
    ](self, owner_obj: T | None, owner_type: type[T] | None = None) -> (
        AttrType | ty.Self
    ):
        if owner_obj is not None:
            return self

        if owner_type is None:
            raise RuntimeError("both owner object and owner type is not provided")

        if isinstance(self._name_or_getter, ty.Callable):
            _val = self._name_or_getter(owner_type)
        else:
            try:
                _val: AttrType = getattr(owner_type, self._name_or_getter)
            except AttributeError as ae:
                if self._default is not MISSING:
                    self._default = ty.cast(AttrType, self._default)
                    return self._default
                raise ae
        return _val


