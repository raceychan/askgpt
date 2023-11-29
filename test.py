import typing as ty


class Abstract(ty.Protocol):
    class IInner(ty.Protocol):
        something: str

    inner: IInner


class Concrete:
    class Inner:
        somethings: str

    inner: Inner


concrete: Abstract = Concrete()
