from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.asynchronous.database import AsyncDatabase

from server.core.security import decode_access_token
from server.models.user import UserInDB
from server.repositories.user_repo import UserRepository
from server.services.auth_service import AuthService
from shared.db import get_database

_bearer = HTTPBearer(auto_error=False)


def get_db() -> AsyncDatabase:
    return get_database()


def get_user_repository(
    db: Annotated[AsyncDatabase, Depends(get_db)],
) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(users)


async def get_current_user(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UserInDB:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token: str = creds.credentials
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from exc
    user = await users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user no longer exists")
    return user
