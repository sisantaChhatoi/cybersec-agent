from pymongo.asynchronous.database import AsyncDatabase

from server.models.user import UserInDB


class UserRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self._col = db["users"]

    async def ensure_indexes(self) -> None:
        await self._col.create_index("user_id", unique=True)
        await self._col.create_index("phone_no", unique=True)

    async def insert(self, user: UserInDB) -> None:
        await self._col.insert_one(user.model_dump())

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        doc = await self._col.find_one({"user_id": user_id})
        return UserInDB(**doc) if doc else None

    async def get_by_phone(self, phone_no: str) -> UserInDB | None:
        doc = await self._col.find_one({"phone_no": phone_no})
        return UserInDB(**doc) if doc else None

    async def set_push_token(self, user_id: str, push_token: str) -> None:
        await self._col.update_one(
            {"user_id": user_id}, {"$set": {"push_token": push_token}}
        )
