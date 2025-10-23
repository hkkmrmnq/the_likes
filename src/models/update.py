from pydantic import BaseModel

from .contact_n_message import (
    ContactRead,
    ContactRequestsRead,
    OtherProfileRead,
    UnreadMessagesCount,
)
from .profile_and_user import ProfileRead


class Update(BaseModel):
    recommendations: list[OtherProfileRead]
    contact_requests: ContactRequestsRead | None
    unread_message_counts: UnreadMessagesCount


class FullUpdate(Update):
    my_profile: ProfileRead
    contacts: list[ContactRead]
