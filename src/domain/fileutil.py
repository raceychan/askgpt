import abc
import pathlib
import typing as ty

# def value_parser(val: str) -> ty.Any:
#     """
#     parse a string to a python object

#     Examples:
#     ------
#     >>> value_parser("3.5") -> 3.5
#     >>> value_parser("3") -> 2
#     >>> value_parser("0.0.1") -> '0.0.1'
#     """
#     if val[0] in {'"', "'"}:  # Removing quotes if they exist
#         if val[0] == val[-1]:
#             val = val[1:-1]
#         else:
#             raise ValueError(f"{val} inproperly quoted")

#     # Type casting
#     if val.isdecimal():
#         value = int(val)  # Integer type
#     elif val.lower() in {"true", "false"}:
#         value = val.lower() == "true"  # Boolean type
#     elif val.lower() == "null":
#         value = None
#     else:
#         if val[0].isdecimal():  # Float type
#             try:
#                 value = float(val)
#             except ValueError:
#                 pass
#             else:
#                 return value
#         value = val  # Otherwise, string type
#     return value


class EndOfChainError(Exception):
    ...


class NotDutyError(Exception):
    ...


from typing import TypeVar

TNode = TypeVar("TNode", bound="LoaderNode")


class LoaderNode(abc.ABC):
    _handle_chain: ty.ClassVar[list[type["FileLoader"]]] = list()

    def __init__(self) -> None:
        self._next_handler: ty.Optional["LoaderNode"] = None

    def set_next(self, handler: "FileLoader") -> None:
        self._next_handler = handler

    def append_node(self, handler: "FileLoader") -> None:
        if self._next_handler is None:
            self.set_next(handler)
            return

        node = self._next_handler
        while node._next_handler is not None:
            node = node._next_handler
        node.set_next(handler)

    def reverse(self) -> None:
        """
        Reverse the whole chain so that the last node becomes the first node
        Do this when you want your newly added subclass take over the chain
        """
        raise NotImplementedError  # TODO: implement this
        # reff: https://www.prepbytes.com/blog/python/python-program-to-reverse-a-linked-list/

    @property
    def next_handler(self) -> ty.Optional["LoaderNode"]:
        return self._next_handler

    @abc.abstractmethod
    def _validate(self, file: pathlib.Path) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        raise NotImplementedError

    def validate(self, file: pathlib.Path) -> None:
        if not file.is_file() or not file.exists():
            raise FileNotFoundError(f"File {file} not found")
        self._validate(file)

    def handle(self, file: pathlib.Path) -> dict[str, ty.Any]:
        try:
            self.validate(file)
        except NotDutyError as ne:
            if self._next_handler is None:
                raise EndOfChainError from ne
            result = self._next_handler.handle(file)
        else:
            result = self.loads(file)
        return result


class FileLoader(LoaderNode):
    def _validate(self, file: pathlib.Path) -> None:
        raise NotDutyError

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        raise NotImplementedError

    def __init_subclass__(cls: type["FileLoader"]) -> None:
        cls._handle_chain.append(cls)

    @classmethod
    def from_chain(cls) -> ty.Self:
        head = cls()

        for loader in cls._handle_chain:
            node = loader()
            head.append_node(node)
        return head


# class ENVFileLoader(FileLoader):
#     def _validate(self, file: pathlib.Path) -> None:
#         if not file.name.endswith(".env"):
#             raise NotDutyError

#     def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
#         config: dict[str, ty.Any] = {}
#         ln = 1

#         with file.open() as f:
#             for line in f:
#                 line = line.strip()
#                 if line and not line.startswith("#"):
#                     try:
#                         key, value = line.split("=", 1)
#                         config[key.strip()] = value_parser(value.strip())
#                     except ValueError as ve:
#                         raise Exception(f"Invalid env line number {ln}: {line}") from ve
#                 ln += 1
#         return config


class TOMLFileLoader(FileLoader):
    def _validate(self, file: pathlib.Path) -> None:
        if not file.name.endswith(".toml"):
            raise NotDutyError

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        import sys

        if sys.version_info.minor < 11:
            raise NotImplementedError

        import tomllib as tomli

        config = tomli.loads(file.read_text())
        return config


# class YAMLFileLoader(FileLoader):
#     def _validate(self, file: pathlib.Path) -> None:
#         if not file.name.endswith(".yml") or not file.name.endswith(".yaml"):
#             raise NotDutyError

#     def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
#         import yaml

#         config: dict[str, ty.Any] = yaml.safe_load(file.read_bytes())
#         return config


class FileUtil:
    def __init__(self, work_dir: pathlib.Path, file_loader: FileLoader):
        self.work_dir = work_dir
        self.file_loader = file_loader

    def find(self, filename: str, dir: str | None = None) -> pathlib.Path:
        work_dir = pathlib.Path(dir) if dir is not None else self.work_dir
        rg = work_dir.rglob(filename)
        try:
            file = next(rg)
        except StopIteration as se:
            raise FileNotFoundError(
                f"File '{filename}' not found in current directory {work_dir}"
            ) from se
        return file

    def read_file(self, file: str | pathlib.Path) -> dict[str, ty.Any]:
        if isinstance(file, str):
            file = self.find(file)
        return self.file_loader.handle(file)

    @classmethod
    def from_cwd(cls) -> ty.Self:
        return cls(work_dir=pathlib.Path.cwd(), file_loader=FileLoader.from_chain())


fileutil = FileUtil.from_cwd()
