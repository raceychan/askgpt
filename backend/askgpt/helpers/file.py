import abc
import typing as ty
from pathlib import Path

from askgpt.helpers.functions import simplecache


def relative_path(file: str) -> str:
    file_path = Path(file).relative_to(Path.cwd())
    return str(file_path).replace("/", ".")[:-3]


class EndOfChainError(Exception): ...


class NotDutyError(Exception): ...


class UnsupportedFileFormatError(Exception):
    def __init__(self, file: Path):
        super().__init__(
            f"File of format {file.suffix} is not supported, as dependency is not installed"
        )


class LoaderNode(abc.ABC):
    @abc.abstractmethod
    def _validate(self, file: Path) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def loads(self, file: Path) -> dict[str, ty.Any]:
        raise NotImplementedError


class FileLoader(LoaderNode):
    _handle_chain: ty.ClassVar[list[type["FileLoader"]]] = list()
    supported_formats: ty.ClassVar[set[str] | str]

    def __init__(self) -> None:
        self._next: "FileLoader | None" = None

    def __init_subclass__(cls: type["FileLoader"]) -> None:
        cls._handle_chain.append(cls)

    def __str__(self):
        return f"{self.__class__.__name__}({self.supported_formats})"

    def __repr__(self):
        return self.__str__()

    @property
    def next(self) -> "FileLoader | None":
        return self._next

    @next.setter
    def next(self, handler: "FileLoader | None") -> None:
        self._next = handler

    def validate(self, file: Path) -> bool:
        if not file.is_file() or not file.exists():
            raise FileNotFoundError(f"File {file} not found at {Path.cwd()}")
        return self._validate(file)

    def _validate(self, file: Path) -> bool:
        supported = self.supported_formats
        if isinstance(supported, str):
            supported = {supported}
        return file.suffix in supported or file.name in supported

    def handle(self, file: Path) -> dict[str, ty.Any]:
        if self.validate(file):
            return self.loads(file)

        if self._next is None:
            raise EndOfChainError

        return self._next.handle(file)

    def chain(self, handler: "FileLoader") -> "FileLoader | None":
        if self._next is None:
            self._next = handler
            return self._next

        return self._next.chain(handler)

    def reverse(self) -> None:
        """
        Reverse the whole chain so that the last node becomes the first node
        Do this when you want your newly added subclass take over the chain
        """
        prev = None
        node = self

        while node.next:
            next = node.next
            node.next = prev
            prev = node
            node = next

        node.next = prev

    @classmethod
    def register(cls, loader: type["FileLoader"]) -> None:
        cls._handle_chain.append(loader)

    @classmethod
    def from_chain(cls, reverse: bool = True) -> "FileLoader":
        loaders = [loader_cls() for loader_cls in cls._handle_chain]

        if reverse:
            loaders = list(reversed(loaders))

        head = node = loaders[0]

        for loader in loaders[1:]:
            node.next = loader
            node = loader
        return head


class ENVFileLoader(FileLoader):
    supported_formats = ".env"

    def loads(self, file: Path) -> dict[str, ty.Any]:
        try:
            import dotenv
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        return dotenv.dotenv_values(file)


class TOMLFileLoader(FileLoader):
    supported_formats = ".toml"

    def loads(self, file: Path) -> dict[str, ty.Any]:
        try:
            import tomllib as tomli  # tomllib available ^3.11
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config = tomli.loads(file.read_text())
        return config


class YAMLFileLoader(FileLoader):
    supported_formats = {".yml", ".yaml"}

    def loads(self, file: Path) -> dict[str, ty.Any]:
        try:
            import yaml
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config: dict[str, ty.Any] = yaml.safe_load(file.read_bytes())
        return config


class JsonFileLoader(FileLoader):
    supported_formats = ".json"

    def loads(self, file: Path) -> dict[str, ty.Any]:
        try:
            import json
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config: dict[str, ty.Any] = json.loads(file.read_bytes())
        return config


class FileUtil:
    def __init__(
        self,
        work_dir: Path,
        *,
        file_loader: FileLoader = FileLoader.from_chain(),
    ):
        self.work_dir = work_dir
        self.file_loader = file_loader

    def __repr__(self):
        return f"{self.__class__.__name__}(work_dir={self.work_dir})"

    def search(
        self, pattern: str, *, dir: str | Path | None = None, recursive: bool = True
    ) -> Path | None:
        work_dir = Path(dir) if dir else self.work_dir

        if recursive:
            rg = work_dir.rglob(pattern)
        else:
            rg = work_dir.glob(pattern)
        try:
            file = next(rg)
        except StopIteration as se:
            return None
        return file

    def find(
        self, pattern: str, *, dir: str | Path | None = None, recursive: bool = True
    ) -> Path:
        work_dir = Path(dir) if dir else self.work_dir
        if recursive is True:
            for file in work_dir.rglob(pattern):
                return file
        else:
            files = work_dir.iterdir()
            for file in files:
                if file == pattern:
                    return work_dir / file
        raise FileNotFoundError(
            f"File '{pattern}' not found in current directory {work_dir}"
        )

    def read_file(self, file: str | Path) -> dict[str, ty.Any]:
        if isinstance(file, str):
            file = self.find(file)
        try:
            data = self.file_loader.handle(file)
        except EndOfChainError as ee:
            raise UnsupportedFileFormatError(file) from ee
        return data

    @classmethod
    @simplecache
    def from_cwd(cls) -> ty.Self:
        return cls(work_dir=Path.cwd(), file_loader=FileLoader.from_chain())


fileutil = FileUtil.from_cwd()
