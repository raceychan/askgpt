import re

pattern_uppercase = re.compile(r"([A-Z]+)")
pattern_camel_case = re.compile(r"([A-Z][a-z]+)")


def str_to_snake(string: str) -> str:
    """
    Examples:
    -------
    >>> snake_case("myCamelName") == my_variable_name"
    assert snake_case("snake-case-example") == "snake_case_example"
    assert snake_case("AnotherExample123") == "another_example123"
    assert snake_case("PascalCase") == "camel_case"
    """
    string = string.replace("-", " ")

    # Apply the compiled patterns
    string = pattern_uppercase.sub(r" \1", string)
    snake_string = pattern_camel_case.sub(r" \1", string).lower()

    # Join and convert to snake_case
    snake_string = "_".join(snake_string.split())
    return snake_string


def pascal_to_snake(string: str):
    "works for both camelCase and PascalCase"
    if not string:
        return string
    return "".join(["_" + c.lower() if c.isupper() else c for c in string]).lstrip("_")


def snake_to_pascal(snake_string: str):
    words = snake_string.split("_")
    pascal_string = "".join([word.capitalize() for word in words])
    return pascal_string



