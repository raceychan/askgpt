from src.domain import enums


def test_enum_generator():
    enum_gen = enums.enum_generator(Color=["red", "green", "blue"])
    Color = next(enum_gen)
    assert issubclass(Color, enums.Enum)
    assert isinstance(Color.red, Color)
    assert Color.red.value == "red"


