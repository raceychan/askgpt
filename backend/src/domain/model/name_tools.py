import re

pattern_uppercase = re.compile(r"([A-Z]+)")
pattern_camel_case = re.compile(r"([A-Z][a-z]+)")


def str_to_snake(string: str) -> str:
    """
    Examples:
    -------
    >>> str_to_snake("myCamelName") == my_camel_name"
    assert str_to_snake("snake-case-example") == "snake_case_example"
    assert str_to_snake("AnotherExample123") == "another_example123"
    assert str_to_snake("PascalCase") == "pascal_case"
    """
    string = string.replace("-", " ")

    # Apply the compiled patterns
    string = pattern_uppercase.sub(r" \1", string)
    snake_string = pattern_camel_case.sub(r" \1", string).lower()

    # Join and convert to snake_case
    snake_string = "_".join(snake_string.split())
    return snake_string


def snake_to_pascal(snake_string: str) -> str:
    words = snake_string.split("_")
    pascal_string = "".join([word.capitalize() for word in words])
    return pascal_string
