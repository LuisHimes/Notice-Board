from fastapi import APIRouter

from ..dependencies import Users
from ..dependencies.auth import HRUser, StaffUser
from ..dependencies.authorization import Policy
from ..models.user import Role
from ..schemas.user import TraineeCreate, UserView
from .common import Limit, Offset

router = APIRouter(tags=["Onboarding"])


@router.post("/trainees", response_model=UserView, status_code=201)
def onboard_trainee(data: TraineeCreate, service: Users, actor: HRUser, policy: Policy):
    policy.require_actor(data.onboarded_by_id)
    return service.onboard(data)


@router.get("/trainees", response_model=list[UserView])
def list_trainees(service: Users, actor: StaffUser, offset: Offset = 0, limit: Limit = 100):
    return service.list_trainees(offset=offset, limit=limit)


@router.get("/trainees/{trainee_id}", response_model=UserView)
def get_trainee(trainee_id: int, service: Users, policy: Policy):
    policy.require_trainee_access(trainee_id)
    return service.require_role(trainee_id, Role.trainee)