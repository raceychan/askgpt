import grpc
from llama_pb2 import CompletionRequest
from llama_pb2_grpc import CompletionServiceStub

# from proto.user_defined_protos_pb2 import UserDefinedMessage


def request(address: str, question: str):
    channel = grpc.insecure_channel(address)
    stub = CompletionServiceStub(channel)
    com_req = CompletionRequest(question=question)
    return stub.Complete(request=com_req)


if __name__ == "__main__":
    address = "localhost:9000"
    q = "Q: give me a example of python iterator? A: "
    comp = request(address, q)
    print(comp)
