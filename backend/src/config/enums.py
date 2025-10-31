from enum import Enum

from sqlalchemy.dialects.postgresql import ENUM


class Polarity(str, Enum):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'


PolarityPG = ENUM(
    *[p.value for p in Polarity],
    name='polarity_enum',
    create_type=True,
)


class ContactStatus(str, Enum):
    REQUESTED_BY_ME = 'requested by me'
    REQUESTED_BY_OTHER = 'requested by the other user'
    CANCELLED_BY_ME = 'cancelled by me'
    CANCELLED_BY_OTHER = 'cancelled by the other user'
    REJECTED_BY_ME = 'rejected by me'
    REJECTED_BY_OTHER = 'rejected by the other user'
    ONGOING = 'ongoing'
    BLOCKED_BY_ME = 'blocked by me'
    BLOCKED_BY_OTHER = 'blocked by the other user'


ContactStatusPG = ENUM(
    *[s.value for s in ContactStatus],
    name='contact_status_enum',
    create_type=True,
)


class SearchAllowedStatus(str, Enum):
    OK = 'ok'
    COOLDOWN = 'cooldown'
    SUSPENDED = 'suspended'


SearchAllowedStatusPG = ENUM(
    *[s.value for s in SearchAllowedStatus],
    name='search_allowed_status',
    create_type=True,
)
