from ..models.progress_report import ProgressReport
from ..models.user import Role
from ..repositories.progress_report import ProgressReportRepository
from ..schemas.progress_report import FeedbackCreate, ReportCreate
from .assignment import AssignmentService
from .base import BaseService, WorkflowError
from .notification import NotificationService
from .plan import PlanService
from .user import UserService


class ProgressReportService(BaseService[ProgressReportRepository]):
    def __init__(
        self, repository: ProgressReportRepository, assignments: AssignmentService,
        plans: PlanService, users: UserService, notifications: NotificationService,
    ):
        super().__init__(repository)
        self.assignments = assignments
        self.plans = plans
        self.users = users
        self.notifications = notifications

    def submit_report(self, assignment_id: int, data: ReportCreate) -> ProgressReport:
        assignment = self.assignments.get_assignment(assignment_id)
        if assignment.trainee_id != data.trainee_id:
            raise WorkflowError("Only the assigned trainee can submit progress", 403)
        report = self.repository.add(ProgressReport(
            assignment_id=assignment_id, progress=data.progress, summary=data.summary,
        ))
        assignment.progress = data.progress
        self.repository.save()
        return report

    def list_reports(self, assignment_id: int, *, offset: int = 0, limit: int = 100) -> list[ProgressReport]:
        self.assignments.get_assignment(assignment_id)
        return self.repository.for_assignment(assignment_id, offset=offset, limit=limit)

    def give_feedback(self, report_id: int, data: FeedbackCreate) -> ProgressReport:
        self.users.require_role(data.manager_id, Role.manager)
        report = self.require(ProgressReport, report_id)
        assignment = self.assignments.get_assignment(report.assignment_id)
        plan = self.plans.get_plan(assignment.plan_id)
        if plan.manager_id != data.manager_id:
            raise WorkflowError("Only the plan manager can review this report", 403)
        report.feedback = data.feedback
        report.reviewed_by_id = data.manager_id
        self.notifications.notify(assignment.trainee_id, f"Feedback received for: {plan.title}")
        self.repository.save()
        return report