from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services import chat_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await chat_manager.start_up()
    yield
    await chat_manager.shut_down()
