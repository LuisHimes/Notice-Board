from datetime import datetime

from .base import View


class NotificationView(View):
    id: int
    trainee_id: int
    message: str
    is_read: bool
    created_at: datetime