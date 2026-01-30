from dataclasses import dataclass, field
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class PublicPaths:
    REGISTER: str = '/register'
    VERIFY_EMAIL: str = '/verify-email'
    REQUEST_EMAIL_VERIFICATION: str = '/request-email-verification'
    LOGIN: str = '/login'
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


default_language = getenv('DEFAULT_LANGUAGE')
translate_to = getenv('TRANSLATE_TO')
supported_languages = f'{default_language}, {translate_to}'


@dataclass(frozen=True)
class Config:
    PATHS: Paths = Paths()
    BASIC_DATA_PATH: str = 'Basic data.xlsx'
    PERSONAL_VALUE_MAX_ORDER: int = 11  # == total number of values
    # Here and after - must raise.
    DEFAULT_LANGUAGE: str = default_language  # type: ignore
    TRANSLATE_TO: list[str] = field(
        default_factory=lambda: translate_to.split(', ')  # type: ignore
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
    POSTGRES_USER: str = getenv('POSTGRES_USER')  # type: ignore
    POSTGRES_PASSWORD: str = getenv('POSTGRES_PASSWORD')  # type: ignore
    POSTGRES_HOST: str = getenv('POSTGRES_HOST')  # type: ignore
    POSTGRES_PORT: int = int(getenv('POSTGRES_PORT'))  # type: ignore
    POSTGRES_DB: str = getenv('POSTGRES_DB')  # type: ignore
    JWT_SECRET: str = getenv('JWT_SECRET')  # type: ignore
    JWT_ACCESS_LIFETIME_MINUTES: int = int(
        getenv('JWT_ACCESS_LIFETIME_MINUTES')  # type: ignore
    )
    JWT_ALGORITHM: str = getenv('JWT_ALGORITHM')  # type: ignore
    RESET_PASSWORD_TOKEN_SECRET: str = getenv(
        'RESET_PASSWORD_TOKEN_SECRET'  # type: ignore
    )
    VERIFICATION_TOKEN_SECRET: str = getenv(
        'VERIFICATION_TOKEN_SECRET'  # type: ignore
    )
    EMAIL_APP_EMAIL: str = getenv('EMAIL_APP_EMAIL')  # type: ignore
    EMAIL_APP_NAME: str = getenv('EMAIL_APP_NAME')  # type: ignore
    EMAIL_APP_PASSWORD: str = getenv('EMAIL_APP_PASSWORD')  # type: ignore
    REDIS_HOST: str = getenv('REDIS_HOST')  # type: ignore
    REDIS_PORT: int = int(getenv('REDIS_PORT'))  # type: ignore
    REDIS_DB: int = int(getenv('REDIS_DB'))  # type: ignore
    LOG_PATH: str = getenv('LOG_PATH')  # type: ignore
    BACKEND_ORIGIN: str = getenv('BACKEND_ORIGIN')  # type: ignore
    FRONTEND_ORIGIN: str = getenv('FRONTEND_ORIGIN')  # type: ignore

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8'}

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

    REDIS_URL: str = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT: str = (
        f'user_order <= {PERSONAL_VALUE_MAX_ORDER}'
    )


CFG = Config()
