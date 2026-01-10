from typing import Literal

from pydantic import BaseModel, Field

from src.config.config import CFG


class PersonalAttitude(BaseModel):
    attitude_id: int
    statement: str
    chosen: bool


class PersonalAspectRead(BaseModel):
    aspect_id: int
    aspect_key_phrase: str
    aspect_statement: str
    included: bool

    model_config = {'from_attributes': True}


class PersonalAspectCreate(BaseModel):
    aspect_id: int
    included: bool


class PersonalValueRead(BaseModel):
    value_id: int
    value_name: str
    polarity: str
    user_order: int
    aspects: list[PersonalAspectRead]

    model_config = {'from_attributes': True}


class PersonalValueCreate(BaseModel):
    value_id: int
    polarity: Literal['positive', 'negative', 'neutral']
    user_order: int = Field(ge=1, le=CFG.PERSONAL_VALUE_MAX_ORDER)
    aspects: list['PersonalAspectCreate']


class PersonalValueUpdate(PersonalValueCreate):
    pass


class PersonalValuesRead(BaseModel):
    initial: bool
    attitudes: list[PersonalAttitude]
    value_links: list[PersonalValueRead]


class PersonalValuesCreateUpdate(BaseModel):
    attitude_id: int
    value_links: list[PersonalValueCreate]
