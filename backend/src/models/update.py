from pydantic import BaseModel

from src.models.contact_n_message import (
    ContactRead,
    ContactRequestsRead,
    OtherProfileRead,
)
from src.models.user_and_profile import ProfileRead


class UpdateRead(BaseModel):
    my_profile: ProfileRead
    ongoing_contacts: list[ContactRead]
    contact_requests: ContactRequestsRead
    recommendations: list[OtherProfileRead]
