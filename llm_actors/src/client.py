"""
For debug only, service should be called from askgpt client  
"""

import grpc

from llama_pb2 import CompletionRequest
from llama_pb2_grpc import CompletionServiceStub


def request(address: str, question: str):
    channel = grpc.insecure_channel(address)
    stub = CompletionServiceStub(channel)
    com_req = CompletionRequest(question=question)
    return stub.Complete(request=com_req)


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9000
    address = f"{host}:{port}"
    question = input("question: ") or "hello"

    content = f"Q: {question}? A: "
    comp = request(address, content)
    print(comp)
