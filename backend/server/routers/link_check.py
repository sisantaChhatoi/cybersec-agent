"""Link safety checker — scoring lives in chatbot/link_safety.py, shared with the chat tool."""

from fastapi import APIRouter, Depends

from server.chatbot.link_safety import assess_url
from server.deps import get_current_user

router = APIRouter(prefix="/link-check", tags=["link-check"])

_INTERNAL_FIELDS = ("reasons", "checked")


@router.post("")
async def check_link(
    payload: dict,
    _: str = Depends(get_current_user),
) -> dict:
    url: str = payload.get("url", "").strip()
    if not url:
        return {"error": "url is required"}

    assessment = await assess_url(url)
    return {k: v for k, v in assessment.items() if k not in _INTERNAL_FIELDS}
