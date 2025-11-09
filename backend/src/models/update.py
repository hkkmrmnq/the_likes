from pydantic import BaseModel

from src.models.contact_n_message import (
    ContactRead,
    ContactRequestsRead,
    OtherProfileRead,
    UnreadMessagesCount,
)
from src.models.user_and_profile import ProfileRead


class UpdateRead(BaseModel):
    recommendations: list[OtherProfileRead]
    contact_requests: ContactRequestsRead | None
    unread_message_counts: UnreadMessagesCount


class FullUpdate(UpdateRead):
    my_profile: ProfileRead
    contacts: list[ContactRead]
