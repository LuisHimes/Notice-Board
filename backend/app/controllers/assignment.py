from fastapi import APIRouter

from ..dependencies import Assignments
from ..dependencies.auth import CurrentUser, ManagerUser
from ..dependencies.authorization import Policy
from ..models.user import Role
from ..schemas.assignment import AssignmentCreate, AssignmentView
from .common import Limit, Offset

router = APIRouter(tags=["Assignments"])


@router.post("/plans/{plan_id}/assignments", response_model=list[AssignmentView], status_code=201)
def assign_plan(plan_id: int, data: AssignmentCreate, service: Assignments, actor: ManagerUser, policy: Policy):
    policy.require_plan(plan_id)
    return service.assign(plan_id, data)


@router.get("/trainees/{trainee_id}/assignments", response_model=list[AssignmentView])
def list_assignments(
    trainee_id: int, service: Assignments, actor: CurrentUser, policy: Policy,
    offset: Offset = 0, limit: Limit = 100,
):
    policy.require_trainee_access(trainee_id)
    return service.list_assignments(
        trainee_id, offset=offset, limit=limit,
        manager_id=actor.id if actor.role == Role.manager.value else None,
    )