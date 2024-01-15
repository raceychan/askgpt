import typing as ty

type AnyCallable = ty.Callable[..., ty.Any]
type StrDict = dict[str, ty.Any]
type LifeSpan = ty.AsyncContextManager[None]