from sqlalchemy import select

from ..models.cohort import Cohort
from ..models.membership import Membership
from .base import Repository


class CohortRepository(Repository):
    def list_cohorts(
        self, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None, trainee_id: int | None = None,
    ) -> list[Cohort]:
        conditions = []
        if manager_id is not None:
            conditions.append(Cohort.manager_id == manager_id)
        if trainee_id is not None:
            conditions.append(Cohort.id.in_(select(Membership.cohort_id).where(Membership.trainee_id == trainee_id)))
        return self.list(Cohort, offset=offset, limit=limit, conditions=conditions)