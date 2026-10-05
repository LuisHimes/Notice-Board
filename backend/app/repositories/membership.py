from ..models.membership import Membership
from .base import Repository


class MembershipRepository(Repository):
    def list_members(self, cohort_id: int, *, offset: int = 0, limit: int = 100) -> list[Membership]:
        return self.list(Membership, cohort_id=cohort_id, offset=offset, limit=limit)

    def trainee_ids(self, cohort_id: int) -> list[int]:
        return [member.trainee_id for member in self.all(Membership, cohort_id=cohort_id)]