from typing import Annotated

from fastapi import APIRouter, Depends

from server.deps import get_call_repository, get_current_user
from server.models.user import UserInDB
from shared.models.call import CallStats, CallSummary
from shared.repositories.call_repo import CallRepository

router = APIRouter(prefix="/calls", tags=["calls"])

_UserDep = Annotated[UserInDB, Depends(get_current_user)]
_RepoDep = Annotated[CallRepository, Depends(get_call_repository)]


@router.get("/stats", response_model=CallStats)
async def call_stats(user: _UserDep, repo: _RepoDep) -> CallStats:
    return await repo.stats_for_user(user.user_id)


@router.get("", response_model=list[CallSummary])
async def recent_calls(
    user: _UserDep, repo: _RepoDep, limit: int = 20
) -> list[CallSummary]:
    return await repo.recent_for_user(user.user_id, min(limit, 100))
