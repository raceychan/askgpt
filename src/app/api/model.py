from pydantic import BaseModel, ConfigDict


class RequestBody(BaseModel):
    model_config = ConfigDict(frozen=True)
