"""
NOTE: according to hexagon architecture
we could combine modules in this package
and the infra package together as adapters

modules in this package are driving adatpers
modules in the infra package are driven adapters
"""
# from typing import Generic, TypeVar

# T = TypeVar("T", int, str, bytes)


# class UUID(Generic[T]):
#     _uuid: T

#     @property
#     def uuid(self) -> T:
#         return self._uuid


# class StrUUID(UUID[str]):
#     _uuid: str


# class IntUUID(UUID[int]):
#     _uuid: int


# class BytesUUID(UUID[bytes]):
#     _uuid: bytes
