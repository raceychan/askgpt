import grpc
from llama_pb2 import CompletionRequest
from llama_pb2_grpc import CompletionServiceStub

# from proto.user_defined_protos_pb2 import UserDefinedMessage


channel = grpc.insecure_channel("localhost:9000")
stub = CompletionServiceStub(channel)
request = CompletionRequest(question="Q: at what templerature will water freeze? A: ")

if __name__ == "__main__":
    comp = stub.Complete(request=request)
    print(comp.completion)
