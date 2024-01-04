from src.infra.timer import FuncInfo, timeit


@timeit
def add_two(a: int, b: int) -> int:
    return a + b


class Test:
    @timeit
    def add_two(self, a: int, b: int) -> int:
        return a + b


@timeit
async def add_three(a: int, b: int, c: int) -> int:
    return a + b + c


assert add_two(2, 3) == 5
assert Test().add_two(1, 2) == 3
