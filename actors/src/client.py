import grpc
from proto.user_defined_protos_pb2 import UserDefinedMessage
from proto.user_defined_protos_pb2_grpc import UserDefinedServiceStub

channel = grpc.insecure_channel("localhost:9000")
stub = UserDefinedServiceStub(channel)
request = UserDefinedMessage(name="foo", num=50, origin="bar")

if __name__ == "__main__":
    response, call = stub.__call__.with_call(request=request)
    print(f"status code: {call.code()}")  # grpc.StatusCode.OK
    print(f"greeting: {response.greeting}")  # "Hello foo from bar"
    print(f"num: {response.num}")  # 60


