from dataclasses import dataclass
from datetime import datetime, time
from uuid import UUID

from src.config import ENM


@dataclass
class RichContactRead:
    my_user_id: UUID
    other_user_id: UUID
    my_name: str | None
    other_name: str | None
    status: ENM.ContactStatus
    distance: float | None
    similarity: float
    unread_msg: int
    created_at: datetime


@dataclass
class ContactRead:
    user_id: UUID
    name: UUID
    similarity: float
    distance: float


@dataclass
class ContactWrite:
    my_user_id: UUID
    other_user_id: UUID
    status: ENM.ContactStatus


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
class AuthResult:
    subject: str | None
    detail: ENM.AuthResultDetail
