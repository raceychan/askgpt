from sys import stdout


def fprint(string: str):
    """
    fast alternative to print(string, end="", flush=True)
    (tested for > 1000 iteration)
    """

    stdout.write(string)
    stdout.flush()
