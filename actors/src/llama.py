from llama_cpp import Llama

MODEL = "llama-2-7b.Q4_K_M"
MODEL_PATH = f"./models/{MODEL}.gguf"


def load_model(model_path: str = MODEL_PATH):
    llm = Llama(model_path=model_path)
    return llm

def complete(llm: Llama, prompt: str):
    output = llm(
        prompt,
        max_tokens=32,
        stop=["Q:", "\n"],
        echo=False
    )
    for choice in output["choices"]:
        yield choice.text


if __name__ == "__main__":
    llm = load_model()
    output = complete(llm, "Q: Name the planets in the solar system? A: ")
    print(output)
