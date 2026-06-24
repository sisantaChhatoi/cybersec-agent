from datetime import datetime, timezone

from server.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from server.models.user import UserCreate, UserInDB, new_user_id
from server.repositories.user_repo import UserRepository


class UserAlreadyExistsError(Exception):
    def __init__(self, field: str) -> None:
        super().__init__(field)
        self.field = field


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def signup(self, data: UserCreate) -> tuple[UserInDB, str]:
        if await self._users.get_by_phone(data.phone_no):
            raise UserAlreadyExistsError("phone_no")
        user = UserInDB(
            user_id=new_user_id(),
            created_at=datetime.now(timezone.utc),
            password_hash=hash_password(data.password),
            **data.model_dump(exclude={"password"}),
        )
        await self._users.insert(user)
        return user, create_access_token(user.user_id)

    async def login(self, phone_no: str, password: str) -> tuple[UserInDB, str]:
        user = await self._users.get_by_phone(phone_no)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        return user, create_access_token(user.user_id)
