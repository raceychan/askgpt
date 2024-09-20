import re
import typing as ty

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


class KeySpace(
    ty.NamedTuple
):  # use namedtuple for memory efficiency, can use __slots__ instead
    """Organize key to create redis key namespace
    >>> KeySpace("base")("new").key
    'base:new'
    >>> (Keyspace("key") / "new").key
    'key:new'
    """

    key: str = ""

    def __iter__(self):
        # fun fact: this is slower than str.split
        left, right, end = 0, 1, len(self.key)

        while right < end:
            if self.key[right] == ":":
                yield self.key[left:right]
                left = right + 1
            right += 1
        yield self.key[left:right]

    def __call__(self, next_part: str) -> "KeySpace":
        if not self.key:
            return KeySpace(next_part)
        return KeySpace(f"{self.key}:{next_part}")

    def __truediv__(self, other: "str | KeySpace") -> "KeySpace":
        if isinstance(other, self.__class__):
            return KeySpace(self.key + ":" + other.key)

        if isinstance(other, str):
            return KeySpace(self.key + ":" + other)

        raise TypeError

    @property
    def parent(self):
        return KeySpace(self.key[: self.key.rfind(":")])

    @property
    def base(self):
        return KeySpace(self.key[: self.key.find(":")])

    def add_cls(self, cls: type, with_module: bool = True) -> "KeySpace":
        """
        Generate key space for class, under current keyspace
        >>> Keyspace("test").add_cls(Test)
        test:module:test
        """
        if with_module:
            key = f"{cls.__module__}:{str_to_snake(cls.__name__)}"
        else:
            key = str_to_snake(cls.__name__)
        return self(key)
