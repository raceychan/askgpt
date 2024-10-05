import typing as ty

from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel, ConfigDict
from starlette import status


class DTO(BaseModel):
    """
    [refer](https://martinfowler.com/eaaCatalog/dataTransferObject.html)
    Data classes that has no domain logic.
    Encapsulating the de/serialization mechanism.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid",
        use_enum_values=True,
        populate_by_name=True,
    )


class RequestBody(DTO):
    """
    In a restful api design
    Path is used to locate the entity, e.g: /users/{user_id}
    Query is used to search the entity, e.g: /users?name=race
    Body is used to carry information about the entity
    """

    ...


class ResponseData(DTO):
    """
    Isolating the changes happen on domain object
    """

    ...



OK = Response(status_code=status.HTTP_200_OK)
EntityDeleted = Response(status_code=status.HTTP_204_NO_CONTENT)
