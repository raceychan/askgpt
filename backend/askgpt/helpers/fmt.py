import typing as ty
from sys import stdout


def fprint(string: str) -> None:
    """
    fast alternative to print(string, end="", flush=True)
    (tested for > 1000 iteration), ~30%
    """

    stdout.write(string)
    stdout.flush()


async def async_receiver(answer: ty.AsyncGenerator[str | None, None]) -> str:
    # TODO: either print or return value at a time, not both
    str_container = ""
    async for chunk in answer:
        if chunk is None:
            fprint("\n")
        else:
            fprint(chunk)
            str_container += chunk
    return str_container
