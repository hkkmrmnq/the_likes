from enum import Enum

from sqlalchemy.dialects.postgresql import ENUM

USER_NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_MIN_SCORE = 3
EMAIL_MAX_LENGTH = 320
LOCATION_MAX_LENGTH = 29
VALUE_NAME_MAX_LENGTH = 100
SUBDEF_KEY_PHRASE_MAXLENGTH = 250
SUBDEF_STATEMENT_MAX_LENGTH = 500
UNIQUE_VALUE_MIN_ORDER = 1
UNIQUE_VALUE_MAX_ORDER = 11  # == total number of value names
MAX_USER_ORDER_CONSTRAINT_TEXT = f'user_order <= {UNIQUE_VALUE_MAX_ORDER}'
MIN_USER_ORDER_CONSTRAINT_TEXT = f'user_order >= {UNIQUE_VALUE_MIN_ORDER}'
# how many top positive UVs should match to consider profiles alike
NUMBER_OF_BEST_UVS = 2
NUMBER_OF_WORST_UVS = 2
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
APP_DOMAIN = 'yourfrontend.com'
URL_MAX_LENGTH = 2048
ATTITUDE_TEXT_MAX_LENGTH = 500
LANGUAGE_DEFAULT = 'en'
SUPPORTED_LANGUAGES = [LANGUAGE_DEFAULT, 'ru']
LANGUAGES_CHECK_CONSTRAINT_TEXT = f'languages <@ ARRAY[{", ".join(f"'{c}'" for c in SUPPORTED_LANGUAGES)}]::varchar[]'  # noqa
DISTANCE_LIMIT_MAX = 20037509  # earth semicircle
MESSAGE_MAX_LENGTH = 2000
COMMON_RESPONSES = {
    400: {'description': 'Incorrect body structure.'},
    401: {'description': 'Unauthorized.'},
    403: {'description': 'Unverified / inactive account.'},
    404: {'description': 'Requested item not found'},
    409: {'description': 'Item(s) already exist(s).'},
    500: {'description': 'Something went wrong.'},
}
MESSAGES_HISTORY_LENGTH_DEFAULT = 20
MATERIALIZED_VIEW_NAMES = (
    'pv_aggregated',
    'similarity_scores',
    'recommendations',
)
RECOMMENDATIONS_UPDATE_INTERVAL_HOURS = 4


class ContactStatus(str, Enum):
    AWAITS = 'awaits'
    REJECTED = 'rejected'
    ONGOING = 'ongoing'
    CLOSED = 'closed'


ContactStatusEnum = ENUM(
    *[status.value for status in ContactStatus],
    name='contact_status_enum',
    create_type=True,
)
