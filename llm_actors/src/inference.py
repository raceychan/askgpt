import typing as ty
from pathlib import Path

from llama_cpp import Llama
from rich import print

from src.config import Config


def load_model(model_path: Path) -> Llama:
    llm = Llama(model_path=str(model_path))
    return llm


def complete(
    llm: Llama, prompt: str, *, max_tokens: int, stream: bool = False
) -> ty.Iterator[str]:
    output = llm(
        prompt, max_tokens=max_tokens, stop=["Q:", "\n"], echo=False, stream=stream
    )
    if not isinstance(output, ty.Iterator):
        output = [output]

    for item in output:
        for choice in item["choices"]:
            text = choice["text"]
            yield text


def main(config: Config):
    if not config.MODEL_PATH.exists():
        raise ValueError("model path not found")
    llm = load_model(config.MODEL_PATH)
    output = complete(
        llm,
        "Q: Name the planets in the solar system?, list out their names A: ",
        max_tokens=500,
        stream=True,
    )
    ans = ""
    for s in output:
        ans += s
    print(ans)


if __name__ == "__main__":
    main(Config())
