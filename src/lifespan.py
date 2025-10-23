from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src import crud
from src.crud import sql
from src.sessions import a_session_factory, async_engine


async def check_basic_data():
    async with a_session_factory() as session:
        await crud.read_definitions(a_session=session)
        await crud.read_attitudes(a_session=session)


async def manage_precalculations():
    async with a_session_factory() as session:
        for query in sql.prepare_recommendations_raw_str:
            await session.execute(text(query))
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_basic_data()
    await manage_precalculations()
    yield
    await async_engine.dispose()
