from typing import Any

from pydantic import BaseModel

from src.config.enums import ContactStatus


class ErrorResponse(BaseModel):
    detail: str
    extra: dict[str, Any] | None = None


COMMON_RESPONSES = {
    400: {
        'model': ErrorResponse,
        'description': 'Incorrect body structure.',
        'content': {
            'application/json': {
                'example': {'detail': 'Incorrect body structure.'}
            }
        },
    },
    401: {
        'model': ErrorResponse,
        'description': 'Unauthorized / inactive account.',
        'content': {
            'application/json': {
                'example': {'detail': 'Unauthorized / inactive account.'}
            }
        },
    },
    403: {
        'model': ErrorResponse,
        'description': 'Unverified',
        'content': {'application/json': {'example': {'detail': 'Unverified'}}},
    },
    404: {'description': 'Requested item not found'},
    409: {'description': 'Item(s) already exist(s).'},
    500: {'description': 'Something went wrong.'},
}

USER_NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_MIN_SCORE = 3
EMAIL_MAX_LENGTH = 320
LOCATION_MAX_LENGTH = 29
VALUE_NAME_MAX_LENGTH = 100
SUBDEF_KEY_PHRASE_MAXLENGTH = 250
SUBDEF_STATEMENT_MAX_LENGTH = 500
# how many top positive UVs should match to consider profiles alike
NUMBER_OF_BEST_UVS = 2
NUMBER_OF_WORST_UVS = 2
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
APP_DOMAIN = 'yourfrontend.com'
URL_MAX_LENGTH = 2048
ATTITUDE_TEXT_MAX_LENGTH = 500
UQ_CNSTR_CONTACT_MY_USER_ID_TARGET_USER_ID = (
    'unique_contact_my_user_id_other_user_id'
)
DISTANCE_LIMIT_KM_MAX = 20037.509
MESSAGE_MAX_LENGTH = 2000
BLOCKABLE_CONTACT_STATUSES = [
    ContactStatus.ONGOING,
    ContactStatus.REJECTED_BY_ME,
    ContactStatus.REQUESTED_BY_OTHER,
]
MESSAGES_HISTORY_LENGTH_DEFAULT = 20
MATCH_NOTIFIED_REDIS_KEY = 'match_notified'
