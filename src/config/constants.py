from datetime import timedelta

# from celery.schedules import crontab
from src.config.enums import ContactStatus

USER_NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_MIN_SCORE = 3
EMAIL_MAX_LENGTH = 320
LOCATION_MAX_LENGTH = 29
VALUE_NAME_MAX_LENGTH = 100
SUBDEF_KEY_PHRASE_MAXLENGTH = 250
SUBDEF_STATEMENT_MAX_LENGTH = 500
PERSONAL_VALUE_MIN_ORDER = 1
PERSONAL_VALUE_MAX_ORDER = 11  # == total number of value names
PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT = (
    f'user_order <= {PERSONAL_VALUE_MAX_ORDER}'
)
PERSONAL_VALUE_MIN_ORDER_CONSTRAINT_TEXT = (
    f'user_order >= {PERSONAL_VALUE_MIN_ORDER}'
)
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
DISTANCE_LIMIT_MAX = 20037509
MESSAGE_MAX_LENGTH = 2000
COMMON_RESPONSES = {
    400: {'description': 'Incorrect body structure.'},
    401: {'description': 'Unauthorized / inactive account.'},
    403: {'description': 'Unverified.'},
    404: {'description': 'Requested item not found'},
    409: {'description': 'Item(s) already exist(s).'},
    500: {'description': 'Something went wrong.'},
}
MESSAGES_HISTORY_LENGTH_DEFAULT = 20
RECOMMENDATIONS_AT_A_TIME = 1

IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND = 3
BLOCKABLE_CONTACT_STATUSES = [
    ContactStatus.ONGOING,
    ContactStatus.REJECTED_BY_ME,
    ContactStatus.REQUESTED_BY_OTHER,
]
UNIQUE_CONTACT_MY_USER_ID_TARGET_USER_ID = (
    'unique_contact_my_user_id_other_user_id'
)
MATCH_NOTIFIED_REDIS_KEY = 'match_notified'
# COOLDOWN_DURATION = timedelta(days=1)
# REFRESH_MATERIALIZED_VIEWS_EVERY = timedelta(hours=1)
# NOTIFY_MATCHES_AT = crontab(hour=12, minute=00)
# UPDATE_MATCH_NOTIFICATION_COUNTERS_AT = crontab(hour=12, minute=10)
# SUSPEND_AT = crontab(hour=23, minute=00)
# END_COOLDOWNS_EVERY = timedelta(hours=1)

# ####################### CELERY TEST
COOLDOWN_DURATION = timedelta(seconds=60)
REFRESH_MATERIALIZED_VIEWS_EVERY = timedelta(seconds=15)
NOTIFY_MATCHES_AT = timedelta(seconds=60)
UPDATE_MATCH_NOTIFICATION_COUNTERS_AT = timedelta(seconds=60)
SUSPEND_AT = timedelta(seconds=60)
END_COOLDOWNS_EVERY = timedelta(seconds=60)
