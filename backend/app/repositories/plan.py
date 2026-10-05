from sqlalchemy import select

from ..models.assignment import Assignment
from ..models.plan import Plan
from .base import Repository


class PlanRepository(Repository):
    def list_plans(
        self, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None, trainee_id: int | None = None,
    ) -> list[Plan]:
        conditions = []
        if manager_id is not None:
            conditions.append(Plan.manager_id == manager_id)
        if trainee_id is not None:
            conditions.append(Plan.id.in_(select(Assignment.plan_id).where(Assignment.trainee_id == trainee_id)))
        return self.list(Plan, offset=offset, limit=limit, conditions=conditions)