from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.repositories.chat_repo import ChatRepository
from server.repositories.user_repo import UserRepository
from server.routers import auth, chatbot
from shared.db import get_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_database()
    await UserRepository(db).ensure_indexes()
    await ChatRepository(db).ensure_indexes()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ScamCall API", lifespan=lifespan)
    app.include_router(auth.router)
    app.include_router(chatbot.router)
    return app


app = create_app()
