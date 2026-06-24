from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from server.deps import get_auth_service, get_current_user
from server.models.user import (
    AuthResponse,
    LoginRequest,
    UserCreate,
    UserInDB,
    UserPublic,
)
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
