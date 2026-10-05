from typing import Annotated

from fastapi import Depends

from ..services.membership import MembershipService
from .cohort import Cohorts
from .repositories import MembershipRepositoryDep
from .user import Users


def get_membership_service(
    repository: MembershipRepositoryDep,
    cohorts: Cohorts,
    users: Users,
) -> MembershipService:
    return MembershipService(repository=repository, cohorts=cohorts, users=users)


Memberships = Annotated[MembershipService, Depends(get_membership_service)]