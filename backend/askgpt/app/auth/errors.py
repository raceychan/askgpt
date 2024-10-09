from askgpt.app.api.errors import EntityNotFoundError, GeneralWebError

"""
TODO: split into UserError, AuthError
class UserError(APPErrorBase):
    instance = "/users/{user_id}"

    def __init__(self, user_id: str):

        super().__init__(
            msg="User {user_id} not found", instance=instance.format(user_id=user_id)
        )

"""


class ServiceError(GeneralWebError):
    service: str


class AuthenticationError(GeneralWebError):
    """
    Failed to authenticate user
    """

    service: str = "auth"


class UserNotRegisteredError(AuthenticationError):
    """
    Unable to find user with the email provided
    """

    def __init__(self, *, user_email: str):
        msg = f"user with email:{user_email} is not found"
        super().__init__(msg)


class UserNotFoundError(EntityNotFoundError, AuthenticationError):
    """
    Unable to find user with the same user id
    """

    def __init__(self, *, user_id: str):
        msg = f"user {user_id} is not found"
        super().__init__(msg)


class UserInactiveError(EntityNotFoundError, AuthenticationError):
    """
    User is not active
    """

    def __init__(self, *, user_id: str):
        msg = f"user {user_id} is not active"
        instance = f"/users/{user_id}"
        super().__init__(msg, instance=instance)


class InvalidEmailAddressError(AuthenticationError):
    """
    User email is not a valid email address
    """

    def __init__(self, *, email: str):
        super().__init__(f"{email} is not a valid email address")


class InvalidPasswordError(AuthenticationError):
    """
    User email and password does not match
    """


class UserAlreadyExistError(AuthenticationError):
    """
    User with the same email already exist
    """

    def __init__(self, *, email: str):
        super().__init__(f"User with {email=} already exist")


class InvalidCredentialError(AuthenticationError):
    """
    Could not validate user credentials
    """


class UserAPIKeyNotProvidedError(AuthenticationError):
    """
    User API key not provided
    """

    def __init__(self, *, user_id: str, api_type: str):
        msg = f"user {user_id} api key not provided for {api_type}"
        super().__init__(msg)
