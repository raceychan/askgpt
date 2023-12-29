from pathlib import Path

from llama import MODEL, complete, load_model
from llama_pb2 import CompletionRequest, CompletionResponse
from ray import serve


@serve.deployment
class GrpcDeployment:
    def __init__(self, model_path: str):
        self.llm = load_model(model_path)

    def Complete(self, request: CompletionRequest) -> CompletionResponse:
        output = complete(self.llm, request.question)
        print("output: ", output)
        return CompletionResponse(completion=output)


if __name__ == "__main__":
    model_path = Path.cwd() / "models" / f"{MODEL}.gguf"
    g = GrpcDeployment.bind(str(model_path))
    app1 = "app1"
    serve.run(target=g, name=app1, route_prefix=f"/{app1}")
