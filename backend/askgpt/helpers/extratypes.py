import typing as ty

type AnyCallable = ty.Callable[..., ty.Any]
type StrDict = dict[str, ty.Any]
type LifeSpan = ty.AsyncContextManager[None]


class _Sentinel: ...


SENTINEL = _Sentinel()


def issentinel(obj: ty.Any) -> bool:
    """
    check if an object is the SENTINEL object
    """
    return isinstance(obj, _Sentinel) and obj is SENTINEL
