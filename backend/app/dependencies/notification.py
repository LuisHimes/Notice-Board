from typing import Annotated

from fastapi import Depends

from ..services.notification import NotificationService
from .repositories import NotificationRepositoryDep
from .user import Users


def get_notification_service(
    repository: NotificationRepositoryDep,
    users: Users,
) -> NotificationService:
    return NotificationService(repository=repository, users=users)


Notifications = Annotated[NotificationService, Depends(get_notification_service)]