from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..config import constants as CNST


class RecomendationRead(BaseModel):
    """
    Model for reading Rows retrived from 'recommendations' mat. view.
    Not for API usage.
    """

    similar_profile_id: int
    similarity_score: float
    distance_meters: float | None = None

    @field_validator('similarity_score', mode='before')
    def round_similarity_score(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v

    class Config:
        from_attributes = True


class ContactRead(BaseModel):
    name: str | None
    status: CNST.ContactStatus
    similarity_score: float
    distance: float | None
    me_ready_to_start: bool
    user_id: UUID
    created_at: datetime

    class Config:
        arbitrary_types_allowed = True


class ContactsRead(BaseModel):
    found: bool
    contacts: list[ContactRead | None] = []


class AgreeSchema(BaseModel):
    user_id: UUID


class InfoMessage(BaseModel):
    message: str


class ContactUnreadMessagesCount(BaseModel):
    sender_id: UUID
    number: int


class UnreadMessagesTotalCount(BaseModel):
    total: int
    contacts: list[ContactUnreadMessagesCount]


class MessageCreate(BaseModel):
    receiver_id: UUID
    content: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)


class MessageRead(BaseModel):
    id: int
    sender_id: UUID
    sender_name: str | None
    receiver_id: UUID
    receiver_name: str | None
    content: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)
    created_at: datetime

    class Config:
        from_attributes = True
