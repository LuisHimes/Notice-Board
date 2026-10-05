from ..models.notification import Notification
from .base import Repository


class NotificationRepository(Repository):
    def for_trainee(self, trainee_id: int, *, offset: int = 0, limit: int = 100) -> list[Notification]:
        return self.list(Notification, trainee_id=trainee_id, offset=offset, limit=limit)