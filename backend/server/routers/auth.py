from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from server.deps import get_auth_service, get_current_user, get_user_repository
from server.models.user import (
    AuthResponse,
    LoginRequest,
    PushTokenRequest,
    UserCreate,
    UserInDB,
    UserPublic,
)
from server.repositories.user_repo import UserRepository
from server.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_ServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(data: UserCreate, service: _ServiceDep) -> AuthResponse:
    try:
        user, token = await service.signup(data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"{exc.field} already registered"
        ) from exc
    return AuthResponse(access_token=token, user=UserPublic(**user.model_dump()))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, service: _ServiceDep) -> AuthResponse:
    try:
        user, token = await service.login(data.phone_no, data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "invalid phone number or password"
        ) from exc
    return AuthResponse(access_token=token, user=UserPublic(**user.model_dump()))


@router.get("/me", response_model=UserPublic)
async def me(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    return current_user


@router.post("/push-token", status_code=status.HTTP_204_NO_CONTENT)
async def register_push_token(
    data: PushTokenRequest,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> None:
    await users.set_push_token(current_user.user_id, data.push_token)
