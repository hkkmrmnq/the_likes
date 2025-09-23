from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from . import constants as cnst
from . import crud
from .db import engine, session_factory
from .scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with session_factory() as session:
        await session.execute(select(1))
        await crud.read_definitions(cnst.LANGUAGE_DEFAULT, session)
        await crud.read_attitudes(cnst.LANGUAGE_DEFAULT, session)
        if await crud.similarity_scores_exists(session):
            await session.execute(crud.sql.refresh_mat_view_similarity_scores)
        else:
            await crud.create_similarity_scores(session)
        if await crud.recommendations_exists(session):
            await session.execute(crud.sql.refresh_mat_view_recommendations)
        else:
            await crud.create_recommendations(session)
        await session.commit()
    scheduler = start_scheduler(session_factory)
    yield
    scheduler.shutdown(wait=False)
    await engine.dispose()
