import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from server.deps import get_current_user, get_notification_service
from server.models.user import UserInDB
from server.services.notification_service import NotificationService, PushError
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])


@router.post("/notify")
async def notify(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    notifier: Annotated[NotificationService, Depends(get_notification_service)],
) -> dict:
    logger.info(
        "test notify: resolved phone %s for user %s",
        current_user.phone_no,
        current_user.user_id,
    )

    if not current_user.push_token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "no push token registered for this user",
        )

    try:
        await notifier.send_push(
            current_user.push_token,
            title="Scam alert (test)",
            body=f"Test notification for {settings.test_notification_phone}",
            data={"type": "test"},
        )
    except PushError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"push failed: {exc}") from exc

    return {
        "status": "sent",
        "resolved_phone": current_user.phone_no,
        "test_target": settings.test_notification_phone,
    }
