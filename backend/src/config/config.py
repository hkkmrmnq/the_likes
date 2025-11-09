from datetime import timedelta

from celery.schedules import crontab
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    BASIC_DATA_PATH: str = 'Basic data.xlsx'
    PERSONAL_VALUE_MAX_ORDER: int = 11  # == total number of values
    DEFAULT_LANGUAGE: str = 'en'
    TRANSLATE_TO: list[str] = ['ru']
    RECOMMENDATIONS_AT_A_TIME: int = 1
    IGNORED_MATCH_NOTIFICATIONS_BEFORE_SUSPEND: int = 3
    COOLDOWN_DURATION: timedelta = timedelta(days=1)
    REFRESH_MATERIALIZED_VIEWS_EVERY: timedelta = timedelta(minutes=1)
    NOTIFY_MATCHES_AT: crontab = crontab(hour=12, minute=00)
    UPDATE_MATCH_NOTIFICATION_COUNTERS_AT: crontab = crontab(
        hour=12, minute=10
    )
    SUSPEND_AT: crontab = crontab(hour=23, minute=00)
    END_COOLDOWNS_EVERY: timedelta = timedelta(hours=1)
    RANDOM_PV_TEST_ATTEMPTS: int = 100
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    JWT_SECRET: str
    JWT_ACCESS_LIFETIME: int
    RESET_PASSWORD_TOKEN_SECRET: str
    VERIFICATION_TOKEN_SECRET: str
    EMAIL_APP_EMAIL: str
    EMAIL_APP_NAME: str
    EMAIL_APP_PASSWORD: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    BASE_URL_DEV: str

    model_config = {'env_file': '.env', 'env_file_encoding': 'utf-8'}

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:'
            f'{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (
            f'postgresql+psycopg2://{self.POSTGRES_USER}:'
            f'{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    @property
    def REDIS_URL(self) -> str:
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'

    @property
    def SUPPORTED_LANGUAGES(self) -> list[str]:
        return [self.DEFAULT_LANGUAGE] + self.TRANSLATE_TO

    @property
    def PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT(self) -> str:
        return f'user_order <= {self.PERSONAL_VALUE_MAX_ORDER}'


CFG = Settings()  # type: ignore
