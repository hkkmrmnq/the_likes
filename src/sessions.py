from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from .config import CFG

async_engine = create_async_engine(CFG.ASYNC_DATABASE_URL, echo=True)
a_session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)

sync_engine = create_engine(CFG.SYNC_DATABASE_URL, echo=True)
s_session_factory = sessionmaker(sync_engine)
