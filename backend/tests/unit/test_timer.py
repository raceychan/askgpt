import time

from askgpt.helpers.time import FuncInfo, timeit


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


class B:
    @timeit
    def slow_func(self):
        time.sleep(0.01)


fi = FuncInfo.from_func(add_two)
mi = FuncInfo.from_func(B.slow_func)


def test_timeit():
    assert add_two(2, 3) == 5
    assert Test().add_two(1, 2) == 3
    assert B().slow_func() is None
