from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import crud
from .db import engine, session_factory
from .scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await crud.check_basic_data()
    await crud.manage_precalculations()
    scheduler = start_scheduler(session_factory)
    yield
    scheduler.shutdown(wait=False)
    await engine.dispose()
