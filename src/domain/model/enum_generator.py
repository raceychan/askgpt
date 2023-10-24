import typing as ty
from enum import Enum
from src.domain.model.name_tools import str_to_snake


def enum_generator(
    **kwargs: dict[str, ty.Iterable[str]]
) -> ty.Generator[Enum, None, None]:
    """
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
