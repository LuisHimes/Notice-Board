from ..models.user import Role, User
from ..repositories.user import UserRepository
from ..schemas.user import StaffCreate, TraineeCreate
from .base import BaseService, WorkflowError


class UserService(BaseService[UserRepository]):
    def require_role(self, identifier: int, role: Role) -> User:
        user = self.require(User, identifier)
        if user.role != role.value:
            raise WorkflowError(f"User must have the {role.value} role", 403)
        return user

    def create_staff(self, data: StaffCreate) -> User:
        user = self.repository.add(User(**data.model_dump()))
        self.repository.save()
        return user

    def onboard(self, data: TraineeCreate) -> User:
        self.require_role(data.onboarded_by_id, Role.hr)
        trainee = self.repository.add(User(**data.model_dump(), role="trainee"))
        self.repository.save()
        return trainee

    def list_trainees(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        return self.repository.list_trainees(offset=offset, limit=limit)