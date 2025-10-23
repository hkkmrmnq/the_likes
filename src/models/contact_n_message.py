from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..config import constants as CNST
from ..config.enums import ContactStatus


class UserToNotifyOfMatchRead(BaseModel):
    user_id: UUID
    email: EmailStr = Field(max_length=CNST.EMAIL_MAX_LENGTH)


class OtherProfileRead(BaseModel):
    user_id: UUID
    name: str | None
    similarity_score: float
    distance_meters: int

    @field_validator('similarity_score', mode='before')
    def round_similarity_score(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v

    class Config:
        from_attributes = True


class ContactRead(BaseModel):
    user_id: UUID
    name: str | None
    status: ContactStatus
    created_at: datetime

    class Config:
        arbitrary_types_allowed = True


class ContactRequestRead(ContactRead):
    time_waiting: timedelta


class ContactRequestsRead(BaseModel):
    incoming: list[ContactRead]
    outgoing: list[ContactRead]


class TargetUser(BaseModel):
    id: UUID


class UnreadMessagesCountByContact(BaseModel):
    sender_id: UUID
    count: int


class UnreadMessagesCount(BaseModel):
    total: int
    contacts: list[UnreadMessagesCountByContact]


class MessageCreate(BaseModel):
    receiver_id: UUID
    text: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)


class MessageRead(BaseModel):
    sender_id: UUID
    sender_name: str | None
    receiver_id: UUID
    receiver_name: str | None
    text: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)
    created_at: datetime

    class Config:
        from_attributes = True
