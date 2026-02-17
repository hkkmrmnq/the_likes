from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from src.config.config import CFG

sync_engine = create_engine(CFG.SYNC_DATABASE_URL)  # , echo=True
sync_session_factory = sessionmaker(sync_engine)

async_engine = create_async_engine(CFG.ASYNC_DATABASE_URL)  # , echo=True
asession_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_async_session():
    async with asession_factory() as asession:
        async with asession.begin():
            yield asession
