from typing import Annotated

from fastapi import Depends

from ..services.cohort import CohortService
from .repositories import CohortRepositoryDep
from .user import Users


def get_cohort_service(repository: CohortRepositoryDep, users: Users) -> CohortService:
    return CohortService(repository=repository, users=users)


Cohorts = Annotated[CohortService, Depends(get_cohort_service)]