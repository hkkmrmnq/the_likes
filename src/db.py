from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from .config import CFG

engine = create_async_engine(CFG.DATABASE_URL, echo=True)
session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
