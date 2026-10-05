from fastapi import APIRouter

from ..dependencies import Memberships
from ..dependencies.auth import ManagerUser
from ..dependencies.authorization import Policy
from ..schemas.membership import MemberCreate, MemberView
from .common import Limit, Offset

router = APIRouter(tags=["Cohorts"])


@router.post("/cohorts/{cohort_id}/members", response_model=MemberView, status_code=201)
def add_member(cohort_id: int, data: MemberCreate, service: Memberships, actor: ManagerUser, policy: Policy):
    policy.require_cohort(cohort_id)
    return service.add_member(cohort_id, data)


@router.get("/cohorts/{cohort_id}/members", response_model=list[MemberView])
def list_members(cohort_id: int, service: Memberships, policy: Policy, offset: Offset = 0, limit: Limit = 100):
    policy.require_cohort(cohort_id)
    return service.list_members(cohort_id, offset=offset, limit=limit)