import typing as ty

from llama_cpp import Llama

MODEL_NAME = "llama-2-7b.Q4_K_M"
MODEL_PATH = f"./models/{MODEL_NAME}.gguf"


def load_model(model_path: str) -> Llama:
    llm = Llama(model_path=model_path)
    return llm


def complete(llm: Llama, prompt: str, max_tokens: int, stream: bool = False):
    output = llm(
        prompt, max_tokens=max_tokens, stop=["Q:", "\n"], echo=False, stream=stream
    )
    if not isinstance(output, ty.Iterator):
        output = [output]

    for item in output:
        for choice in item["choices"]:
            yield choice["text"]


def main():
    llm = load_model(MODEL_PATH)
    output = complete(
        llm,
        "Q: Name the planets in the solar system?, list out their names A: ",
        500,
        stream=True,
    )
    ans = ""
    for s in output:
        ans += s
    print(ans)


if __name__ == "__main__":
    main()
