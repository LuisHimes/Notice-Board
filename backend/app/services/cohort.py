from ..models.cohort import Cohort
from ..models.user import Role
from ..repositories.cohort import CohortRepository
from ..schemas.cohort import CohortCreate
from .base import BaseService
from .user import UserService


class CohortService(BaseService[CohortRepository]):
    def __init__(self, repository: CohortRepository, users: UserService):
        super().__init__(repository)
        self.users = users

    def get_cohort(self, cohort_id: int) -> Cohort:
        return self.require(Cohort, cohort_id)

    def create_cohort(self, data: CohortCreate) -> Cohort:
        self.users.require_role(data.manager_id, Role.manager)
        cohort = self.repository.add(Cohort(**data.model_dump()))
        self.repository.save()
        return cohort

    def list_cohorts(
        self, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None, trainee_id: int | None = None,
    ) -> list[Cohort]:
        return self.repository.list_cohorts(
            offset=offset, limit=limit, manager_id=manager_id, trainee_id=trainee_id,
        )