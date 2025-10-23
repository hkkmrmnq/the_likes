from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = 'TheLikes dev'
    BASIC_DATA_PATH: str = 'Basic data.xlsx'
    PG_USER: str
    PG_PASSWORD: str
    PG_HOST: str
    PG_PORT: int
    PG_DB_NAME: str
    JWT_SECRET: str
    JWT_ACCESS_LIFETIME: int
    RESET_PASSWORD_TOKEN_SECRET: str
    VERIFICATION_TOKEN_SECRET: str
    EMAIL_APP_EMAIL: str
    EMAIL_APP_NAME: str
    EMAIL_APP_PASSWORD: str
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    @property
    def ASYNC_DATABASE_URL(self):
        return (
            f'postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}'
            f'@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB_NAME}'
        )

    @property
    def SYNC_DATABASE_URL(self):
        return (
            f'postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}'
            f'@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB_NAME}'
        )


def get_settings():
    return Settings()  # type: ignore
