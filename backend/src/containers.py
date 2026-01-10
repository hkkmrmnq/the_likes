from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.config.enums import ContactStatus


@dataclass
class RichContactRead:
    my_user_id: UUID
    other_user_id: UUID
    my_name: str | None
    other_name: str | None
    status: ContactStatus
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
    status: ContactStatus
