import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.chatbot.retrieval import warm as warm_retrieval
from server.graph.scheduler import start_scheduler, stop_scheduler
from server.repositories.chat_repo import ChatRepository
from server.repositories.incident_repo import IncidentRepository
from server.repositories.notification_repo import NotificationRepository
from server.repositories.user_repo import UserRepository
from server.routers import (
    alerts,
    auth,
    calls,
    chatbot,
    intelligence,
    link_check,
    notifications,
    test,
)
from shared.db import get_database

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = get_database()
    await UserRepository(db).ensure_indexes()
    await ChatRepository(db).ensure_indexes()
    await IncidentRepository(db).ensure_indexes()
    await NotificationRepository(db).ensure_indexes()
    try:
        await asyncio.to_thread(warm_retrieval)
        logger.info("knowledge-base index ready")
    except Exception:
        logger.exception("knowledge-base warmup failed; will build lazily on first use")
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(title="ScamCall API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(chatbot.router)
    app.include_router(intelligence.router)
    app.include_router(alerts.router)
    app.include_router(calls.router)
    app.include_router(notifications.router)
    app.include_router(link_check.router)
    app.include_router(test.router)
    return app


app = create_app()
