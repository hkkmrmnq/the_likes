from pydantic import BaseModel

from src.models.contact_n_message import (
    ContactRichRead,
    OtherProfileRead,
)
from src.models.user_and_profile import ProfileRead


class Bootstrap(BaseModel):
    profile: ProfileRead
    active_contacts: list[ContactRichRead]
    contact_requests: list[ContactRichRead]
    recommendations: list[OtherProfileRead]
