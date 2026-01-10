from pydantic import BaseModel

from .contact_n_message import ContactRead, RecommendationRead
from .user_and_profile import ProfileRead


class Bootstrap(BaseModel):
    profile: ProfileRead
    active_contacts: list[ContactRead]
    contact_requests: list[ContactRead]
    recommendations: list[RecommendationRead]


class ActiveContactsAndRequests(BaseModel):
    active_contacts: list[ContactRead]
    contact_requests: list[ContactRead]
