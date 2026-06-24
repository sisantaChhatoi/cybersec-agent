import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger("scamcall.worker")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    logger.info("connected to room %r", ctx.room.name)

    for identity in ctx.room.remote_participants:
        logger.info("participant present: %s", identity)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
