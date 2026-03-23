from datetime import datetime, time, timezone
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from src.config import ENM

from .contact_n_message import (
    ContactRead,
    MessageCreate,
    MessageRead,
    RecommendationRead,
    TargetUser,
)


class MessageError(BaseModel):
    error: str


class MessageSent(BaseModel):
    receiver_id: UUID
    client_id: UUID
    created_at: datetime
    time: time


def validate_iso_timestamp_string(value: str) -> str:
    try:
        datetime.fromisoformat(value)
        return value
    except (TypeError, ValueError):
        raise ValueError(
            'ping_timestamp validation error: '
            'input should be an ISO-formatted timestamp string. '
            f'Input: {value}'
        )


def format_to_zod_timestamp(dt: datetime) -> str:
    """Also removes offset and adds 'Z'."""
    return dt.isoformat().split('+')[0] + 'Z'


def get_now_timestamp_for_zod():
    return format_to_zod_timestamp(datetime.now(timezone.utc))


class HeartbeatDetail(BaseModel):
    origin: ENM.BeatOrigin


TYPE_CONTENT_MAP = {
    ENM.ChatPayloadType.CREATE_MSG: MessageCreate,
    ENM.ChatPayloadType.NEW_MSG: MessageRead,
    ENM.ChatPayloadType.MSG_SENT: MessageSent,
    ENM.ChatPayloadType.MSG_READ: TargetUser,
    ENM.ChatPayloadType.MSG_ERROR: MessageError,
    ENM.ChatPayloadType.PING: HeartbeatDetail,
    ENM.ChatPayloadType.PONG: HeartbeatDetail,
    ENM.ChatPayloadType.NEW_RECOMM: RecommendationRead,
    ENM.ChatPayloadType.NEW_REQUEST: ContactRead,
    ENM.ChatPayloadType.NEW_CHAT: ContactRead,
    ENM.ChatPayloadType.BLOCKED_BY: ContactRead,
}


class ChatPayload(BaseModel):
    payload_type: ENM.ChatPayloadType
    related_content: (
        MessageRead
        | MessageCreate
        | MessageError
        | MessageSent
        | TargetUser
        | HeartbeatDetail
        | RecommendationRead
        | ContactRead
    )
    timestamp: str = Field(default_factory=lambda: get_now_timestamp_for_zod())

    model_config = {'from_attributes': True}

    @field_validator('timestamp', mode='after')
    @classmethod
    def is_iso_formatted(cls, value: str) -> str:
        validate_iso_timestamp_string(value)
        return value

    @model_validator(mode='after')
    def validate_type(self):
        if not isinstance(
            self.related_content, TYPE_CONTENT_MAP[self.payload_type]
        ):
            raise ValueError(
                f'Incorrect message schema for type {self.payload_type}.'
            )
        return self
