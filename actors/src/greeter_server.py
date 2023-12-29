from concurrent import futures

import grpc
from actors.src.proto.greeter_pb2 import HelloReply
from proto.greeter_pb2_grpc import GreeterServicer, add_GreeterServicer_to_server


class Greeter(GreeterServicer):

    def SayHello(self, request, context):
        return HelloReply(message=f"Hello, {request.name}!")

    def SayHelloAgain(self, request, context):
        return HelloReply(message=f"Hello again, {request.name}!")


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
