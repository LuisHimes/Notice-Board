from typing import Annotated

from fastapi import Depends

from ..services.assignment import AssignmentService
from .cohort import Cohorts
from .notification import Notifications
from .plan import Plans
from .repositories import AssignmentRepositoryDep, MembershipRepositoryDep
from .user import Users


def get_assignment_service(
    repository: AssignmentRepositoryDep,
    plans: Plans,
    cohorts: Cohorts,
    memberships: MembershipRepositoryDep,
    users: Users,
    notifications: Notifications,
) -> AssignmentService:
    return AssignmentService(
        repository=repository,
        plans=plans,
        cohorts=cohorts,
        memberships=memberships,
        users=users,
        notifications=notifications,
    )


Assignments = Annotated[AssignmentService, Depends(get_assignment_service)]