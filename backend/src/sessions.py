from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from src.config.config import CFG

sync_engine = create_engine(CFG.SYNC_DATABASE_URL, echo=True)
sync_session_factory = sessionmaker(sync_engine)


def get_sync_session():
    with sync_session_factory() as session:
        yield session


async_engine = create_async_engine(CFG.ASYNC_DATABASE_URL, echo=True)
asession_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator:
    async with asession_factory() as session:
        yield session
