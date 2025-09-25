from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from .config import CNF

engine = create_async_engine(CNF.DATABASE_URL, echo=True)
session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
