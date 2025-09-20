from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

DATABASE_URL = get_settings().database_url
engine = create_async_engine(DATABASE_URL, echo=True)
session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
