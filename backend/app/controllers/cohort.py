from fastapi import APIRouter

from ..dependencies import Cohorts
from ..dependencies.auth import CurrentUser, ManagerUser
from ..dependencies.authorization import Policy
from ..models.user import Role
from ..schemas.cohort import CohortCreate, CohortView
from .common import Limit, Offset

router = APIRouter(tags=["Cohorts"])


@router.post("/cohorts", response_model=CohortView, status_code=201)
def create_cohort(data: CohortCreate, service: Cohorts, actor: ManagerUser, policy: Policy):
    policy.require_actor(data.manager_id)
    return service.create_cohort(data)


@router.get("/cohorts", response_model=list[CohortView])
def list_cohorts(service: Cohorts, actor: CurrentUser, offset: Offset = 0, limit: Limit = 100):
    return service.list_cohorts(
        offset=offset, limit=limit,
        manager_id=actor.id if actor.role == Role.manager.value else None,
        trainee_id=actor.id if actor.role == Role.trainee.value else None,
    )