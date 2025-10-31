from typing import Literal

from pydantic import BaseModel, Field

from src.config import CFG


class PersonalAspectRead(BaseModel):
    aspect_id: int
    aspect_key_phrase: str
    aspect_statement: str
    included: bool

    class Config:
        from_attributes = True


class PersonalAspectCreate(BaseModel):
    aspect_id: int
    included: bool


class PersonalValueRead(BaseModel):
    value_id: int
    value_name: str
    polarity: str
    user_order: int
    aspects: list['PersonalAspectRead']

    class Config:
        from_attributes = True


class PersonalValueCreate(BaseModel):
    value_id: int
    polarity: Literal['positive', 'negative', 'neutral']
    user_order: int = Field(ge=1, le=CFG.PERSONAL_VALUE_MAX_ORDER)
    aspects: list['PersonalAspectCreate']


class PersonalValueUpdate(PersonalValueCreate):
    pass


class PersonalValuesRead(BaseModel):
    attitude_id: int
    attitude_statement: str
    value_links: list[PersonalValueRead]


class PersonalValuesCreateUpdate(BaseModel):
    attitude_id: int
    value_links: list[PersonalValueCreate]
