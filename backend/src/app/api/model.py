from pydantic import BaseModel, ConfigDict


class RequestBody(BaseModel):
    """
    DTO that has no domain logic, use this when there is security concern
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
