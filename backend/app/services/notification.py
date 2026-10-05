from ..models.notification import Notification
from ..models.user import Role
from ..repositories.notification import NotificationRepository
from .base import BaseService, WorkflowError
from .user import UserService


class NotificationService(BaseService[NotificationRepository]):
    def __init__(self, repository: NotificationRepository, users: UserService):
        super().__init__(repository)
        self.users = users

    def notify(self, trainee_id: int, message: str) -> None:
        self.repository.add(Notification(trainee_id=trainee_id, message=message))

    def list_notifications(self, trainee_id: int, *, offset: int = 0, limit: int = 100) -> list[Notification]:
        self.users.require_role(trainee_id, Role.trainee)
        return self.repository.for_trainee(trainee_id, offset=offset, limit=limit)

    def mark_read(self, trainee_id: int, notification_id: int) -> Notification:
        notification = self.require(Notification, notification_id)
        if notification.trainee_id != trainee_id:
            raise WorkflowError("Notification not found", 404)
        notification.is_read = True
        self.repository.save()
        return notification