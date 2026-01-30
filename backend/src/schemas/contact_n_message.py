from datetime import datetime, time, timedelta
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.config import CNST, ENM


class UserToNotifyOfMatchRead(BaseModel):
    user_id: UUID
    email: EmailStr = Field(max_length=CNST.EMAIL_MAX_LENGTH)


class SimilarityAndDistanceMixin(BaseModel):
    similarity: float
    distance: float | None

    @field_validator('similarity', mode='before')
    def round_similarity(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v

    @field_validator('distance', mode='before')
    def round_distance(cls, v):
        if isinstance(v, float):
            return round(v, 2)
        return v


class RecommendationRead(SimilarityAndDistanceMixin, BaseModel):
    user_id: UUID
    name: str | None

    model_config = {'from_attributes': True}


class ContactReadBase(BaseModel):
    user_id: UUID
    name: str | None
    status: ENM.ContactStatus
    created_at: datetime


class ContactRead(SimilarityAndDistanceMixin, ContactReadBase):
    unread_messages: int | None
    time_waiting: timedelta | None


class ContactRequestRead(ContactReadBase):
    time_waiting: timedelta


class ActiveContactsAndRequests(BaseModel):
    active_contacts: list[ContactRead]
    contact_requests: list[ContactRead]


class ContsNReqstsNRecoms(BaseModel):
    recommendations: list[RecommendationRead]
    active_contacts: list[ContactRead]
    contact_requests: list[ContactRead]


class TargetUser(BaseModel):
    id: UUID  # TODO change to user_id


class UnreadMessagesCountByContact(BaseModel):
    sender_id: UUID
    count: int


class UnreadMessagesCount(BaseModel):
    total: int
    contacts: list[UnreadMessagesCountByContact]


class MessageCreate(BaseModel):
    receiver_id: UUID
    text: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)
    client_id: UUID


class MessageRead(BaseModel):
    sender_id: UUID
    sender_name: str | None
    receiver_id: UUID
    receiver_name: str | None
    text: str = Field(max_length=CNST.MESSAGE_MAX_LENGTH)
    created_at: datetime
    time: time

    model_config = {'from_attributes': True}
