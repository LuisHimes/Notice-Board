from fastapi import APIRouter

from ..dependencies import ProgressReports
from ..dependencies.auth import ManagerUser, TraineeUser
from ..dependencies.authorization import Policy
from ..schemas.progress_report import FeedbackCreate, ReportCreate, ReportView
from .common import Limit, Offset

router = APIRouter(tags=["Progress"])


@router.post("/assignments/{assignment_id}/reports", response_model=ReportView, status_code=201)
def submit_report(assignment_id: int, data: ReportCreate, service: ProgressReports, actor: TraineeUser, policy: Policy):
    policy.require_actor(data.trainee_id)
    policy.require_assignment(assignment_id)
    return service.submit_report(assignment_id, data)


@router.get("/assignments/{assignment_id}/reports", response_model=list[ReportView])
def list_reports(assignment_id: int, service: ProgressReports, policy: Policy, offset: Offset = 0, limit: Limit = 100):
    policy.require_assignment(assignment_id)
    return service.list_reports(assignment_id, offset=offset, limit=limit)


@router.patch("/reports/{report_id}/feedback", response_model=ReportView)
def give_feedback(report_id: int, data: FeedbackCreate, service: ProgressReports, actor: ManagerUser, policy: Policy):
    policy.require_actor(data.manager_id)
    policy.require_report(report_id)
    return service.give_feedback(report_id, data)