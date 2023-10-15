import abc
import pathlib
import typing as ty


def value_parser(val: str):
    """
    parse a string to a python object

    Examples:
    ------
    >>> value_parser("3.5") -> 3.5
    >>> value_parser("3") -> 2
    >>> value_parser("0.0.1") -> '0.0.1'
    """
    if val[0] in {'"', "'"}:  # Removing quotes if they exist
        if val[0] == val[-1]:
            val = val[1:-1]
        else:
            raise ValueError(f"{val} inproperly quoted")

    # Type casting
    if val.isdecimal():
        value = int(val)  # Integer type
    elif val.lower() in {"true", "false"}:
        value = val.lower() == "true"  # Boolean type
    elif val.lower() == "null":
        value = None
    else:
        if val[0].isdecimal():  # Float type
            try:
                value = float(val)
            except ValueError as ve:
                pass
            else:
                return value
        value = val  # Otherwise, string type
    return value


class EndOfChainError(Exception):
    ...


class NotDutyError(Exception):
    ...


class LoaderChain(abc.ABC):
    _handle_chain: ty.ClassVar[list[type["FileLoader"]]] = list()
    _next_handler: ty.Optional["FileLoader"] = None

    def set_next(self, handler: "FileLoader"):
        self._next_handler = handler

    def append_node(self, handler: "FileLoader"):
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
    def next_handler(self):
        return self._next_handler

    @abc.abstractmethod
    def _validate(self, file: pathlib.Path) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def loads(self, file: pathlib.Path) -> dict:
        raise NotImplementedError

    def validate(self, file: pathlib.Path):
        if not file.is_file() or not file.exists():
            raise FileNotFoundError(f"File {file} not found")
        self._validate(file)

    def handle(self, file: pathlib.Path):
        try:
            self.validate(file)
        except NotDutyError as ne:
            if self._next_handler is None:
                raise EndOfChainError
            result = self._next_handler.handle(file)
        else:
            result = self.loads(file)
        return result


class FileLoader(LoaderChain):
    def _validate(self, file: pathlib.Path):
        raise NotDutyError

    def loads(self, file: pathlib.Path) -> dict:
        raise NotImplementedError

    def __init_subclass__(cls: type["FileLoader"]):
        return cls._handle_chain.append(cls)

    @classmethod
    def from_chain(cls):
        head = cls()

        for loader in cls._handle_chain:
            node = loader()
            head.append_node(node)
        return head


class ENVFileLoader(FileLoader):
    def _validate(self, file: pathlib.Path):
        if not file.name.endswith(".env"):
            raise NotDutyError

    def loads(self, file: pathlib.Path):
        config = {}
        ln = 1

        with file.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value_parser(value.strip())
                    except ValueError as ve:
                        raise Exception(f"Invalid env line number {ln}: {line}") from ve
                ln += 1
        return config


class TOMLFileLoader(FileLoader):
    def _validate(self, file: pathlib.Path):
        if not file.name.endswith(".toml"):
            raise NotDutyError

    def loads(self, file: pathlib.Path):
        import tomli

        config = tomli.loads(file.read_text())
        return config


class YAMLFileLoader(FileLoader):
    def _validate(self, file: pathlib.Path):
        if not file.name.endswith(".yml") or not file.name.endswith(".yaml"):
            raise NotDutyError

    def loads(self, file: pathlib.Path):
        import yaml

        config = yaml.safe_load(file.read_bytes())
        return config


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

    def read_file(self, file: str | pathlib.Path):
        if isinstance(file, str):
            file = self.find(file)
        return self.file_loader.handle(file)

    @classmethod
    def from_cwd(cls):
        return cls(work_dir=pathlib.Path.cwd(), file_loader=FileLoader.from_chain())


fileutil = FileUtil.from_cwd()
