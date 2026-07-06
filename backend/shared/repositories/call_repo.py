from datetime import datetime, timedelta

from pymongo.asynchronous.database import AsyncDatabase

from shared.models.call import CallRecord, CallStats, CallSummary


class CallRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._col = db["calls"]

    async def ensure_indexes(self) -> None:
        await self._col.create_index("room_name", unique=True)

    async def start(
        self,
        room_name: str,
        *,
        user_phone: str | None,
        user_id: str | None,
        started_at: datetime,
    ) -> None:
        # keyed on room_name; started_at/last_notified_at stick from the first insert
        await self._col.update_one(
            {"room_name": room_name},
            {
                "$setOnInsert": {"started_at": started_at, "last_notified_at": None},
                "$set": {"user_phone": user_phone, "user_id": user_id},
            },
            upsert=True,
        )

    async def end(self, room_name: str, ended_at: datetime) -> None:
        await self._col.update_one(
            {"room_name": room_name}, {"$set": {"ended_at": ended_at}}
        )

    async def claim_notification(
        self, room_name: str, now: datetime, throttle_seconds: float
    ) -> bool:
        # single atomic update so concurrent monitors can't double-notify
        cutoff = now - timedelta(seconds=throttle_seconds)
        res = await self._col.update_one(
            {
                "room_name": room_name,
                "$or": [
                    {"last_notified_at": None},
                    {"last_notified_at": {"$lte": cutoff}},
                ],
            },
            {"$set": {"last_notified_at": now}},
        )
        return res.modified_count == 1

    async def get(self, room_name: str) -> CallRecord | None:
        doc = await self._col.find_one({"room_name": room_name})
        return CallRecord(**doc) if doc else None

    async def stats_for_user(self, user_id: str) -> CallStats:
        scanned = await self._col.count_documents({"user_id": user_id})
        threats_blocked = await self._col.count_documents(
            {"user_id": user_id, "last_notified_at": {"$ne": None}}
        )
        latest = await self._col.find_one(
            {"user_id": user_id},
            sort=[("started_at", -1)],
            projection={"started_at": 1},
        )
        return CallStats(
            scanned=scanned,
            threats_blocked=threats_blocked,
            marked_safe=scanned - threats_blocked,
            last_scanned_at=latest["started_at"] if latest else None,
        )

    async def recent_for_user(self, user_id: str, limit: int) -> list[CallSummary]:
        cursor = self._col.find(
            {"user_id": user_id},
            projection={"started_at": 1, "ended_at": 1, "last_notified_at": 1},
            sort=[("started_at", -1)],
            limit=limit,
        )
        docs = await cursor.to_list(length=limit)
        return [
            CallSummary(
                started_at=d["started_at"],
                ended_at=d.get("ended_at"),
                flagged=d.get("last_notified_at") is not None,
            )
            for d in docs
        ]
