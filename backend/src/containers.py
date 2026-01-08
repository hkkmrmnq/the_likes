from dataclasses import dataclass
from datetime import datetime


@dataclass
class RichContact:
    my_user_id: str
    other_user_id: str
    my_name: str | None
    other_name: str | None
    status: str
    distance: float | None
    similarity: float
    unread_msg: int
    created_at: datetime
