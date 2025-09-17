from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Values dev'
    basic_data_path: str = 'Basic data.xlsx'
    pg_user: str
    pg_password: str
    pg_host: str
    pg_port: int
    pg_db_name: str
    jwt_secret: str
    jwt_access_lifetime: int
    jwt_refresh_lifetime: int
    reset_password_token_secret: str
    verification_token_secret: str
    email_app_email: str
    email_app_name: str
    email_app_password: str
    model_config = SettingsConfigDict(env_file='.env')

    @computed_field(return_type=str)
    @property
    def database_url(self):
        return (
            f'postgresql+asyncpg://{self.pg_user}:{self.pg_password}'
            f'@{self.pg_host}:{self.pg_port}/{self.pg_db_name}'
        )


@lru_cache
def get_settings():
    return Settings()  # type: ignore
