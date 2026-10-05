from typing import Annotated

from fastapi import Depends

from ..services.plan import PlanService
from .notification import Notifications
from .repositories import AssignmentRepositoryDep, PlanRepositoryDep
from .user import Users


def get_plan_service(
    repository: PlanRepositoryDep,
    users: Users,
    assignments: AssignmentRepositoryDep,
    notifications: Notifications,
) -> PlanService:
    return PlanService(
        repository=repository,
        users=users,
        assignments=assignments,
        notifications=notifications,
    )


Plans = Annotated[PlanService, Depends(get_plan_service)]