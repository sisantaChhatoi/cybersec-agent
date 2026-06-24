from contextlib import asynccontextmanager

from fastapi import FastAPI

from server.repositories.user_repo import UserRepository
from server.routers import auth
from shared.db import get_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await UserRepository(get_database()).ensure_indexes()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="ScamCall API", lifespan=lifespan)
    app.include_router(auth.router)
    return app


app = create_app()
