from enum import auto

from askgpt.helpers import enums


def test_enum_generator():
    enum_gen = enums.enum_generator(Color=["red", "green", "blue"])
    Color = next(enum_gen)
    assert issubclass(Color, enums.Enum)
    assert isinstance(Color.red, Color)
    assert Color.red.value == "red"


class Snake(enums.SnakeCaseEnum):
    PythonSnake = auto()


def test_snake_enums():
    assert Snake.PythonSnake.value == "python_snake"
