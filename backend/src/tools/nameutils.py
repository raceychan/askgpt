import re

pattern_uppercase = re.compile(r"([A-Z]+)([A-Z][a-z])")
pattern_camel_case = re.compile(r"([a-z\d])([A-Z])")


def str_to_snake(string: str) -> str:
    """
    Examples:
    -------
    >>> str_to_snake("myCamelName") == my_camel_name"
    assert str_to_snake("snake-case-example") == "snake_case_example"
    assert str_to_snake("AnotherExample123") == "another_example123"
    assert str_to_snake("PascalCase") == "pascal_case"
    """
    string = pattern_uppercase.sub(r"\1_\2", string)
    string = pattern_camel_case.sub(r"\1_\2", string)
    string = string.replace("-", "_")
    return string.lower()


def snake_to_pascal(snake_string: str) -> str:
    words = snake_string.split("_")
    pascal_string = "".join([word.capitalize() for word in words])
    return pascal_string
