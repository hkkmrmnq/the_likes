from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

from src import exceptions as exc

load_dotenv()


def get_env_var_or_raise(var_name: str):
    variable = getenv(var_name)
    if not variable:
        raise exc.ServerError(f'{var_name} env var not found.')
    return variable


@dataclass(frozen=True)
class PublicPaths:
    REGISTER: str = '/register'
    VERIFY_EMAIL: str = '/verify-email'
    FORGOT_PASSWORD: str = '/forgot-password'
    SET_NEW_PASSWORD: str = '/set-new-password'
    REQUEST_EMAIL_VERIFICATION: str = '/request-email-verification'
    LOGIN: str = '/login'
    REFRESH_ACCESS: str = '/refresh-access'
    ABOUT: str = '/about'
    GUIDE: str = '/guide'
    DEFINITIONS: str = '/definitions'


@dataclass(frozen=True)
class PrivatePaths:
    PROFILE: str = '/profile'
    VALUES: str = '/values'
    CONTACTS: str = '/contacts'
    BOOTSTRAP: str = '/bootstrap'
    RECOMMENDATIONS: str = '/check-for-alike'
    UNREAD_MESSAGES_COUNT: str = '/messages/unread-count'
    MESSAGES: str = '/messages'
    CHAT: str = '/ws'  # '/ws/{token}'


@dataclass(frozen=True)
class Paths:
    PUBLIC: PublicPaths = PublicPaths()
    PRIVATE: PrivatePaths = PrivatePaths()


@dataclass(frozen=True)
class ChatConfig:
    MAX_CONNECTIONS: int = 2500
    MAX_QUEUE: int = 20
    RATE_NUMBER: int = 100
    RATE_PERIOD_SECONDS: int = 60
    MAX_MESSAGE_SIZE = 1024 * 1024
    INACTIVITY_MAX_SECONDS = 300
    CLOSE_INACTIVE_EVERY: int = 30


default_language = get_env_var_or_raise('DEFAULT_LANGUAGE')
translate_to = get_env_var_or_raise('TRANSLATE_TO')
supported_languages = f'{default_language}, {translate_to}'


@dataclass(frozen=True)
class Config:
    PATHS: Paths = Paths()
    BASIC_DATA_PATH: str = 'Basic data.xlsx'
    PERSONAL_VALUE_MAX_ORDER: int = 11  # == total number of values
    DEFAULT_LANGUAGE: str = default_language
    TRANSLATE_TO: list[str] = field(
        default_factory=lambda: translate_to.split(', ')
    )
    SUPPORTED_LANGUAGES: list[str] = field(
        default_factory=lambda: supported_languages.split(', ')
    )
    RECOMMENDATIONS_AT_A_TIME: int = 1
    IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND: int = 3
    COOLDOWN_DURATION_HOURS: int = 24
    REFRESH_MATERIALIZED_VIEWS_EVERY_HOURS: int = 4
    NOTIFY_MATCHES_AT_HOUR_MIN: tuple[int, int] = 12, 00
    UPDATE_MATCH_NOTIFICATION_COUNTERS_AT_HOUR_MIN: tuple[int, int] = 13, 20
    SUSPEND_AT_HOUR_MIN: tuple[int, int] = 23, 00
    END_COOLDOWNS_EVERY_HOURS: int = 24
    WS_PING_INTERVAL_SECONDS: int = 20
    RANDOM_PV_TEST_ATTEMPTS: int = 100
    POSTGRES_USER: str = get_env_var_or_raise('POSTGRES_USER')
    POSTGRES_PASSWORD: str = get_env_var_or_raise('POSTGRES_PASSWORD')
    POSTGRES_HOST: str = get_env_var_or_raise('POSTGRES_HOST')
    POSTGRES_PORT: int = int(get_env_var_or_raise('POSTGRES_PORT'))
    POSTGRES_DB: str = get_env_var_or_raise('POSTGRES_DB')
    CONFIRMATION_CODE_LIFETIME_SECONDS = 60
    CONFIRMATION_CODE_LENGTH = 6
    JWT_SECRET: str = get_env_var_or_raise('JWT_SECRET')
    JWT_ACCESS_LIFETIME_MINUTES: int = int(
        get_env_var_or_raise('JWT_ACCESS_LIFETIME_MINUTES')
    )
    JWT_ALGORITHM: str = get_env_var_or_raise('JWT_ALGORITHM')
    REFRESH_TOKEN_LIFETIME_SECONDS: int = 2_592_000  # 30 days
    RESET_PASSWORD_TOKEN_SECRET: str = get_env_var_or_raise(
        'RESET_PASSWORD_TOKEN_SECRET'
    )
    VERIFICATION_TOKEN_SECRET: str = get_env_var_or_raise(
        'VERIFICATION_TOKEN_SECRET'
    )
    EMAIL_APP_EMAIL: str = get_env_var_or_raise('EMAIL_APP_EMAIL')
    EMAIL_APP_NAME: str = get_env_var_or_raise('EMAIL_APP_NAME')
    EMAIL_APP_PASSWORD: str = get_env_var_or_raise('EMAIL_APP_PASSWORD')
    REDIS_HOST: str = get_env_var_or_raise('REDIS_HOST')
    REDIS_PORT: int = int(get_env_var_or_raise('REDIS_PORT'))
    REDIS_MAIN_DB: int = int(get_env_var_or_raise('REDIS_MAIN_DB'))
    REDIS_PUBSUB_DB: int = int(get_env_var_or_raise('REDIS_PUBSUB_DB'))
    LOG_PATH: str = get_env_var_or_raise('LOG_PATH')
    BACKEND_ORIGIN: str = get_env_var_or_raise('BACKEND_ORIGIN')
    FRONTEND_ORIGIN: str = get_env_var_or_raise('FRONTEND_ORIGIN')

    ASYNC_DATABASE_URL: str = (
        f'postgresql+asyncpg://{POSTGRES_USER}:'
        f'{POSTGRES_PASSWORD}'
        f'@{POSTGRES_HOST}:'
        f'{POSTGRES_PORT}/{POSTGRES_DB}'
    )

    SYNC_DATABASE_URL: str = (
        f'postgresql+psycopg2://{POSTGRES_USER}:'
        f'{POSTGRES_PASSWORD}'
        f'@{POSTGRES_HOST}:'
        f'{POSTGRES_PORT}/{POSTGRES_DB}'
    )

    REDIS_MAIN_URL: str = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_MAIN_DB}'
    REDIS_PUBSUB_URL: str = (
        f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_PUBSUB_DB}'
    )

    PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT: str = (
        f'user_order <= {PERSONAL_VALUE_MAX_ORDER}'
    )

    CHAT = ChatConfig()


CFG = Config()
