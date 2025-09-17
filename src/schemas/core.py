from pydantic import BaseModel


class ValueTitleRead(BaseModel):
    id: int
    name: str
    aspects: list['AspectRead']

    class Config:
        from_attributes = True


class AspectRead(BaseModel):
    id: int
    key_phrase: str
    statement: str

    class Config:
        from_attributes = True


class AttitudeRead(BaseModel):
    id: int
    statement: str

    class Config:
        from_attributes = True
