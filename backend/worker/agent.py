import logging

from livekit.agents import JobContext, WorkerOptions, cli

import shared.config  # noqa: F401  (loads .env into the environment on import)

logger = logging.getLogger("scamcall.worker")


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    logger.info("connected to room %r", ctx.room.name)

    for identity in ctx.room.remote_participants:
        logger.info("participant present: %s", identity)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
