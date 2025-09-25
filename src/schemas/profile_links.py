from typing import Literal

from pydantic import BaseModel, Field

from ..config import constants as CNST


class ProfileAspectLinkRead(BaseModel):
    aspect_id: int
    aspect_key_phrase: str
    aspect_statement: str
    included: bool

    class Config:
        from_attributes = True


class ProfileAspectLinkCreate(BaseModel):
    aspect_id: int
    included: bool


class ProfileValueLinkRead(BaseModel):
    value_title_id: int
    value_title_name: str
    polarity: str
    user_order: int
    aspects: list['ProfileAspectLinkRead']

    class Config:
        from_attributes = True


class ProfileValueLinkCreate(BaseModel):
    value_title_id: int
    polarity: Literal['positive', 'negative', 'neutral']
    user_order: int = Field(
        ge=CNST.UNIQUE_VALUE_MIN_ORDER, le=CNST.UNIQUE_VALUE_MAX_ORDER
    )
    aspects: list['ProfileAspectLinkCreate']


class ProfileValueLinkUpdate(ProfileValueLinkCreate):
    pass


class ProfileValuesRead(BaseModel):
    attitude_id: int
    attitude_statement: str
    value_links: list[ProfileValueLinkRead]


class ProfileValuesCreateUpdate(BaseModel):
    attitude_id: int
    value_links: list[ProfileValueLinkCreate]
