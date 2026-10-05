from sqlalchemy import select

from ..models.user import User
from .base import Repository


class UserRepository(Repository):
    def find_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def list_trainees(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        return self.list(User, role="trainee", offset=offset, limit=limit)