# from askgpt.feat.api.errors import EntityNotFoundError, GeneralWebError


# class UserError(GeneralWebError):
#     uri = "/users/{user_id}"

#     def __init__(self, user_id: str):
#         super().__init__(
#             detail="User {user_id} not found", instance=self.uri.format(user_id=user_id)
#         )


# class UserNotFoundError(EntityNotFoundError, UserError):
#     """
#     Unable to find user with the same user id
#     """

#     def __init__(self, *, user_id: str):
#         msg = f"user {user_id} is not found"
#         super().__init__(msg)
