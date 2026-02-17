from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.services import chat_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await chat_manager.create_tasks()
    yield
    await chat_manager.remove_tasks()
