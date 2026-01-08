from datetime import datetime, time, timedelta
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.config import constants as CNST
from src.config.enums import ContactStatus


class UserToNotifyOfMatchRead(BaseModel):
    user_id: UUID
    email: EmailStr = Field(max_length=CNST.EMAIL_MAX_LENGTH)


class OtherProfileRead(BaseModel):
    user_id: UUID
    name: str | None
    similarity: float
    distance: float | None

    @field_validator('similarity', mode='before')
    def round_similarity(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v

    model_config = {'from_attributes': True}


class ContactReadBase(BaseModel):
    user_id: UUID
    name: str | None
    status: ContactStatus
    created_at: datetime

    model_config = {'arbitrary_types_allowed': True}


class ContactRead(ContactReadBase):
    unread_messages: int | None


class ContactRichRead(ContactRead):
    similarity: float
    distance: int | None


class ContactRequestRead(ContactReadBase):
    time_waiting: timedelta


class OngoingContactsAndRequestsRead(BaseModel):
    received_requests: list[ContactRequestRead]
    sent_requests: list[ContactRequestRead]
    active_contacts: list[ContactRead]


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
    time: time

    model_config = {'from_attributes': True}
