from ..models.assignment import Assignment
from ..models.cohort import Cohort
from ..models.plan import Plan
from ..models.progress_report import ProgressReport
from ..models.user import Role, User
from ..repositories.assignment import AssignmentRepository
from ..repositories.base import Model, Repository
from ..repositories.cohort import CohortRepository
from ..repositories.plan import PlanRepository
from ..repositories.progress_report import ProgressReportRepository
from .base import WorkflowError


class AuthorizationService:
    def __init__(
        self, user: User, cohorts: CohortRepository, plans: PlanRepository,
        assignments: AssignmentRepository, reports: ProgressReportRepository,
    ):
        self.user = user
        self.cohorts = cohorts
        self.plans = plans
        self.assignments = assignments
        self.reports = reports

    def require_actor(self, actor_id: int) -> None:
        if actor_id != self.user.id:
            raise WorkflowError("Actor ID must match the authenticated user", 403)

    def require_trainee_access(self, trainee_id: int) -> None:
        if self.user.role == Role.trainee.value:
            self.require_actor(trainee_id)

    def require_record(self, repository: Repository, model: type[Model], identifier: int) -> Model:
        record = repository.get(model, identifier)
        if record is None:
            raise WorkflowError(f"{model.__name__} not found", 404)
        return record

    def require_cohort(self, cohort_id: int) -> Cohort:
        cohort = self.require_record(self.cohorts, Cohort, cohort_id)
        if self.user.role == Role.hr.value:
            return cohort
        if self.user.role == Role.manager.value and cohort.manager_id == self.user.id:
            return cohort
        raise WorkflowError("Access to this cohort is forbidden", 403)

    def require_plan(self, plan_id: int) -> Plan:
        plan = self.require_record(self.plans, Plan, plan_id)
        if self.user.role == Role.hr.value:
            return plan
        if self.user.role == Role.manager.value and plan.manager_id == self.user.id:
            return plan
        if self.user.role == Role.trainee.value and self.assignments.all(
            Assignment, plan_id=plan_id, trainee_id=self.user.id,
        ):
            return plan
        raise WorkflowError("Access to this plan is forbidden", 403)

    def require_assignment(self, assignment_id: int) -> Assignment:
        assignment = self.require_record(self.assignments, Assignment, assignment_id)
        if self.user.role == Role.trainee.value:
            self.require_actor(assignment.trainee_id)
        else:
            self.require_plan(assignment.plan_id)
        return assignment

    def require_report(self, report_id: int) -> ProgressReport:
        report = self.require_record(self.reports, ProgressReport, report_id)
        self.require_assignment(report.assignment_id)
        return report