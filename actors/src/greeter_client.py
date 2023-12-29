import grpc
from actors.src.proto.greeter_pb2 import HelloRequest
from proto.greeter_pb2_grpc import GreeterStub


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = GreeterStub(channel)
        response = stub.SayHello(HelloRequest(name='you'))
        print("Greeter client received: " + response.message)
        response = stub.SayHelloAgain(HelloRequest(name='you'))
        print("Greeter client received: " + response.message)

if __name__ == '__main__':
    run()