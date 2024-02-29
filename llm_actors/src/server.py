from pathlib import Path

from llama import MODEL_NAME, complete, load_model
from llama_pb2 import CompletionRequest, CompletionResponse
from ray import serve
from ray.serve.config import gRPCOptions

grpc_port = 9000
grpc_servicer_functions = [
    "llama_pb2_grpc.add_CompletionServiceServicer_to_server",
]


def start_server():
    grpc_options = gRPCOptions(
        port=grpc_port, grpc_servicer_functions=grpc_servicer_functions
    )
    grpc_options.grpc_servicer_func_callable
    serve.start(
        grpc_port=grpc_port,
        grpc_options=grpc_options,
    )


@serve.deployment
class GrpcDeployment:
    def __init__(self, model_path: str):
        self.llm = load_model(model_path)

    def Complete(self, request: CompletionRequest) -> CompletionResponse:
        output = complete(self.llm, request.question, 500)
        completion = "".join(i for i in output)
        print("completion: ", completion)
        return CompletionResponse(completion=completion)


def deploy():
    model_path = Path.cwd() / "models" / f"{MODEL_NAME}.gguf"
    g = GrpcDeployment.bind(str(model_path))
    app1 = "app1"
    serve.run(target=g, name=app1, route_prefix=f"/{app1}")


if __name__ == "__main__":
    start_server()
    deploy()
