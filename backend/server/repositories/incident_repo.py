from pymongo.asynchronous.database import AsyncDatabase

from server.models.incident import Incident


class IncidentRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._col = db["incidents"]

    async def ensure_indexes(self) -> None:
        await self._col.create_index("session_id", unique=True)

    async def get(self, session_id: str) -> Incident | None:
        doc = await self._col.find_one({"session_id": session_id})
        return Incident(**doc) if doc else None

    async def upsert(self, incident: Incident) -> None:
        await self._col.update_one(
            {"session_id": incident.session_id},
            {"$set": incident.model_dump(mode="json")},
            upsert=True,
        )
