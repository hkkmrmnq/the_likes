from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from . import constants as cnst
from . import crud
from .config import get_settings
from .crud import sql

DATABASE_URL = get_settings().database_url
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def recommendations_mat_view_exists(session: AsyncSession) -> bool:
    """Check if materialized view exists - returns True or False"""
    result = await session.execute(sql.recommendations_exists)
    return bool(result.scalar())


# TODO exceptions, logging
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_maker() as session:
        await session.execute(select(1))
        await crud.read_definitions(cnst.LANGUAGE_DEFAULT, session)
        await crud.read_attitudes(cnst.LANGUAGE_DEFAULT, session)
        await session.execute(sql.create_array_intersect_func)
        await session.execute(sql.create_array_jaccard_similarity_func)
        if await recommendations_mat_view_exists(session):
            await session.execute(sql.refresh_recommendations)
        else:
            await session.execute(sql.create_recommendations_mat_view)
            await session.execute(sql.create_unique_idx_recommendations)
            await session.execute(sql.create_idx_recommendations_profile1)
            await session.execute(sql.create_idx_recommendations_profile2)
        await session.commit()
    yield
    await engine.dispose()
