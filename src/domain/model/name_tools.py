from re import sub


def str_to_snake(string: str) -> str:
    """
    Examples:
    -------
    >>> print(snake_case("myCamelName"))  # Output: "my_variable_name"
    print(snake_case("snake-case-example"))  # Output: "snake_case_example"
    print(snake_case("AnotherExample123"))  # Output: "another_example123"
    print(snake_case("PascalCase"))  # Output: "camel_case"
    """
    snake_string = "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", string.replace("-", " "))
        ).split()
    ).lower()
    return snake_string


def pascal_to_snake(string: str):
    "works for both camelCase and PascalCase"
    if not string:
        return string
    return "".join(["_" + c.lower() if c.isupper() else c for c in string]).lstrip("_")


def snake_to_pascal(snake_string):
    words = snake_string.split("_")
    pascal_string = "".join([word.capitalize() for word in words])
    return pascal_string
