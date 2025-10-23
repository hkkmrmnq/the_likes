from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar('DataT')


class ApiResponse(BaseModel, Generic[DataT]):
    data: DataT | None = None
    message: str | None = None


class AttitudeRead(BaseModel):
    id: int
    statement: str

    class Config:
        from_attributes = True


class AspectRead(BaseModel):
    id: int
    key_phrase: str
    statement: str

    class Config:
        from_attributes = True


class ValueTitleRead(BaseModel):
    id: int
    name: str
    aspects: list[AspectRead]

    class Config:
        from_attributes = True


class DefinitionsRead(BaseModel):
    attitudes: list[AttitudeRead]
    values: list[ValueTitleRead]
