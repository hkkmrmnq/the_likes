from dataclasses import dataclass
from datetime import datetime, time
from uuid import UUID

from src.config import ENM


@dataclass
class ContactBase:
    user_id: UUID
    name: str | None
    distance: float | None
    similarity: float


@dataclass
class ContactRead(ContactBase):
    alias: str | None
    status: ENM.ContactStatus
    unread_messages: int
    created_at: datetime


@dataclass
class ContactWrite:
    my_user_id: UUID
    target_user_id: UUID
    status: ENM.ContactStatus
    alias: str | None


@dataclass
class MessageCreate:
    sender_id: UUID
    receiver_id: UUID
    text: str
    client_id: UUID


@dataclass
class MessageRead:
    sender_id: UUID
    sender_name: str | None
    receiver_id: UUID
    receiver_name: str | None
    text: str
    created_at: datetime
    time: time


@dataclass
class DecodedRefreshToken:
    subject: UUID
    jti: UUID


@dataclass
class MatchToNotify:
    similarity: float
    distance: float | None
    user_id: UUID
    email: str
    match_user_id: UUID
    match_name: str | None
