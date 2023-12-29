# import time
# from typing import Generator

# from proto.user_defined_protos_pb2 import (
#     UserDefinedMessage,
#     UserDefinedMessage2,
#     UserDefinedResponse,
#     UserDefinedResponse2,
# )
from proto.greeter_pb2 import HelloReply, HelloRequest
from ray import serve


@serve.deployment
class GrpcDeployment:
    def SayHello(self, request: HelloRequest, context) -> HelloReply:
        return HelloReply(message=f"Hello, {request.name}!")
    # def __call__(self, user_message: UserDefinedMessage) -> UserDefinedResponse:
    #     greeting = f"Hello {user_message.name} from {user_message.origin}"
    #     num = user_message.num * 2
    #     user_response = UserDefinedResponse(
    #         greeting=greeting,
    #         num=num,
    #     )
    #     return user_response

    # @serve.multiplexed(max_num_models_per_replica=1)
    # async def get_model(self, model_id: str) -> str:
    #     return f"loading model: {model_id}"

    # async def Multiplexing(
    #     self, user_message: UserDefinedMessage2
    # ) -> UserDefinedResponse2:
    #     model_id = serve.get_multiplexed_model_id()
    #     model = await self.get_model(model_id)
    #     user_response = UserDefinedResponse2(
    #         greeting=f"Method2 called model, {model}",
    #     )
    #     return user_response

    # def Streaming(
    #     self, user_message: UserDefinedMessage
    # ) -> Generator[UserDefinedResponse, None, None]:
    #     for i in range(10):
    #         greeting = f"{i}: Hello {user_message.name} from {user_message.origin}"
    #         num = user_message.num * 2 + i
    #         user_response = UserDefinedResponse(
    #             greeting=greeting,
    #             num=num,
    #         )
    #         yield user_response

    #         time.sleep(0.1)


g = GrpcDeployment.bind()

if __name__ == "__main__":
    app1 = "app1"
    serve.run(target=g, name=app1, route_prefix=f"/{app1}")
