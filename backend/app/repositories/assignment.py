from sqlalchemy import select

from ..models.assignment import Assignment
from ..models.plan import Plan
from .base import Repository


class AssignmentRepository(Repository):
    def for_plan(self, plan_id: int) -> list[Assignment]:
        return self.all(Assignment, plan_id=plan_id)

    def for_trainee(
        self, trainee_id: int, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None,
    ) -> list[Assignment]:
        conditions = []
        if manager_id is not None:
            conditions.append(Assignment.plan_id.in_(select(Plan.id).where(Plan.manager_id == manager_id)))
        return self.list(Assignment, trainee_id=trainee_id, offset=offset, limit=limit, conditions=conditions)