import typing as ty
from enum import Enum

from askgpt.helpers.string import str_to_snake

type AnyCallable = ty.Callable[..., ty.Any]
type StrMap = ty.Mapping[str, ty.Any]
type LifeSpan = ty.AsyncContextManager[None]


class _Sentinel: ...


SENTINEL = _Sentinel()


def issentinel(obj: ty.Any) -> bool:
    """
    check if an object is the SENTINEL object
    """
    return isinstance(obj, _Sentinel) and obj is SENTINEL


def enum_generator(
    **kwargs: dict[str, ty.Iterable[str]]
) -> ty.Generator[Enum, None, None]:
    """
    Generate a new Enum class for each keyword argument
    keys would be converted to snake-case



    Example:
    -----
    >>> enum_gen = enum_generator(Color=["red", "green", "blue"])
    Color = next(enum_gen)
    assert issubclass(Color, Enum)
    assert isinstance(Color.red, Color)
    assert Color.red.value == "red"
    """
    for name, values in kwargs.items():
        yield Enum(name, {str_to_snake(v): v for v in values})


class SnakeCaseEnum(str, Enum):
    """
    Enum where members are snake-case strings
    """

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[str]
    ):
        """
        Return the lower-cased version of the member name.
        """
        return str_to_snake(name)
