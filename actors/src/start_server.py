from ray import serve
from ray.serve.config import gRPCOptions

grpc_port = 9000
grpc_servicer_functions = [
    "llama_pb2_grpc.add_CompletionServiceServicer_to_server",
]


def build_options():
    grpc_options = gRPCOptions(
        port=grpc_port, grpc_servicer_functions=grpc_servicer_functions
    )
    grpc_options.grpc_servicer_func_callable
    return grpc_options


def start_server():
    serve.start(
        # http_options={"http_port": 8000},
        grpc_port=grpc_port,
        grpc_options=build_options(),
    )


if __name__ == "__main__":
    start_server()
