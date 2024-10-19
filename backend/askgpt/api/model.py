import typing as ty

from fastapi.responses import RedirectResponse, Response
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
    TODO: we should use typedict for return data
    as they don't need validation.
    but fastapi has bad support for typeddict in terms of
    openapi schema generation

    Isolating the changes happen on domain object
    """

    ...


class _EmptyResponse:
    OK = Response(status_code=status.HTTP_200_OK)
    Created = Response(status_code=status.HTTP_201_CREATED)
    EntityDeleted = Response(status_code=status.HTTP_204_NO_CONTENT)


EmptyResponse = _EmptyResponse()
