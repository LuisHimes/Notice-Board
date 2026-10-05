from fastapi import APIRouter

from ..dependencies import Notifications
from ..dependencies.auth import TraineeUser
from ..dependencies.authorization import Policy
from ..schemas.notification import NotificationView
from .common import Limit, Offset

router = APIRouter(tags=["Notifications"])


@router.get("/trainees/{trainee_id}/notifications", response_model=list[NotificationView])
def list_notifications(trainee_id: int, service: Notifications, actor: TraineeUser, policy: Policy, offset: Offset = 0, limit: Limit = 100):
    policy.require_actor(trainee_id)
    return service.list_notifications(trainee_id, offset=offset, limit=limit)


@router.patch("/trainees/{trainee_id}/notifications/{notification_id}/read", response_model=NotificationView)
def mark_notification_read(trainee_id: int, notification_id: int, service: Notifications, actor: TraineeUser, policy: Policy):
    policy.require_actor(trainee_id)
    return service.mark_read(trainee_id, notification_id)