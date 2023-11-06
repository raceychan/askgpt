from src.domain import snake_to_pascal, str_to_snake


def test_str_to_snake():
    assert str_to_snake("myCamelName") == "my_camel_name"
    assert str_to_snake("snake-case-example") == "snake_case_example"
    assert str_to_snake("AnotherExample123") == "another_example123"
    assert str_to_snake("PascalCase") == "pascal_case"


# def test_pascal_to_snake():
#     assert pascal_to_snake("PascalCase") == "pascal_case"


def test_snake_to_passcal():
    assert snake_to_pascal("pascal_case") == "PascalCase"
