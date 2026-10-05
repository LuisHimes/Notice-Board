from fastapi import APIRouter

from ..dependencies import Plans
from ..dependencies.auth import CurrentUser, ManagerUser
from ..dependencies.authorization import Policy
from ..models.user import Role
from ..schemas.plan import PlanCreate, PlanUpdate, PlanView
from .common import Limit, Offset

router = APIRouter(tags=["Plans"])


@router.post("/plans", response_model=PlanView, status_code=201)
def create_plan(data: PlanCreate, service: Plans, actor: ManagerUser, policy: Policy):
    policy.require_actor(data.manager_id)
    return service.create_plan(data)


@router.get("/plans", response_model=list[PlanView])
def list_plans(service: Plans, actor: CurrentUser, offset: Offset = 0, limit: Limit = 100):
    return service.list_plans(
        offset=offset, limit=limit,
        manager_id=actor.id if actor.role == Role.manager.value else None,
        trainee_id=actor.id if actor.role == Role.trainee.value else None,
    )


@router.get("/plans/{plan_id}", response_model=PlanView)
def get_plan(plan_id: int, service: Plans, policy: Policy):
    policy.require_plan(plan_id)
    return service.get_plan(plan_id)


@router.patch("/plans/{plan_id}", response_model=PlanView)
def update_plan(plan_id: int, data: PlanUpdate, service: Plans, actor: ManagerUser, policy: Policy):
    policy.require_plan(plan_id)
    return service.update_plan(plan_id, data)