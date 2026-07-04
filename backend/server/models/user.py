from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Languages(BaseModel):
    primary: str
    secondary: str | None = None
    tertiary: str | None = None


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    phone_no: str
    password: str = Field(min_length=6)
    state: str
    city: str
    pin: str
    languages: Languages
    age: int = Field(gt=0)


class LoginRequest(BaseModel):
    phone_no: str
    password: str


class UserPublic(BaseModel):
    user_id: str
    name: str
    phone_no: str
    state: str
    city: str
    pin: str
    languages: Languages
    age: int
    created_at: datetime


class UserInDB(UserPublic):
    password_hash: str
    push_token: str | None = None


class PushTokenRequest(BaseModel):
    push_token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


def new_user_id() -> str:
    return uuid4().hex
