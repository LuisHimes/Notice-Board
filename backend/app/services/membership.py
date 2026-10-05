from ..models.membership import Membership
from ..models.user import Role
from ..repositories.membership import MembershipRepository
from ..schemas.membership import MemberCreate
from .base import BaseService
from .cohort import CohortService
from .user import UserService


class MembershipService(BaseService[MembershipRepository]):
    def __init__(self, repository: MembershipRepository, cohorts: CohortService, users: UserService):
        super().__init__(repository)
        self.cohorts = cohorts
        self.users = users

    def add_member(self, cohort_id: int, data: MemberCreate) -> Membership:
        self.cohorts.get_cohort(cohort_id)
        self.users.require_role(data.trainee_id, Role.trainee)
        member = self.repository.add(Membership(cohort_id=cohort_id, trainee_id=data.trainee_id))
        self.repository.save()
        return member

    def list_members(self, cohort_id: int, *, offset: int = 0, limit: int = 100) -> list[Membership]:
        self.cohorts.get_cohort(cohort_id)
        return self.repository.list_members(cohort_id, offset=offset, limit=limit)