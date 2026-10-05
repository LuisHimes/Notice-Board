from typing import Annotated

from fastapi import Depends

from ..services.authorization import AuthorizationService
from .auth import CurrentUser
from .repositories import AssignmentRepositoryDep, CohortRepositoryDep, PlanRepositoryDep, ProgressReportRepositoryDep


def get_authorization_service(
    user: CurrentUser, cohorts: CohortRepositoryDep, plans: PlanRepositoryDep,
    assignments: AssignmentRepositoryDep, reports: ProgressReportRepositoryDep,
) -> AuthorizationService:
    return AuthorizationService(
        user=user, cohorts=cohorts, plans=plans, assignments=assignments, reports=reports,
    )


Policy = Annotated[AuthorizationService, Depends(get_authorization_service)]