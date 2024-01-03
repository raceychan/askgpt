import typing as ty

from llama_cpp import Llama

MODEL = "llama-2-7b.Q4_K_M"
MODEL_PATH = f"./models/{MODEL}.gguf"


def load_model(model_path: str) -> Llama:
    llm = Llama(model_path=model_path)
    return llm


def complete(llm: Llama, prompt: str, stream: bool = False):
    output = llm(prompt, max_tokens=120, stop=["Q:", "\n"], echo=False, stream=stream)
    if not isinstance(output, ty.Iterator):
        output = [output]

    for item in output:
        for choice in item["choices"]:
            yield choice["text"]


if __name__ == "__main__":
    llm = load_model(MODEL_PATH)
    output = complete(llm, "Q: Name the planets in the solar system? A: ", stream=True)
    for i in output:
        print(i)
