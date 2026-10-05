from ..models.assignment import Assignment
from ..models.user import Role
from ..repositories.assignment import AssignmentRepository
from ..repositories.base import ConflictError
from ..repositories.membership import MembershipRepository
from ..schemas.assignment import AssignmentCreate
from .base import BaseService, WorkflowError
from .cohort import CohortService
from .notification import NotificationService
from .plan import PlanService
from .user import UserService


class AssignmentService(BaseService[AssignmentRepository]):
    def __init__(
        self, repository: AssignmentRepository, plans: PlanService,
        cohorts: CohortService, memberships: MembershipRepository,
        users: UserService, notifications: NotificationService,
    ):
        super().__init__(repository)
        self.plans = plans
        self.cohorts = cohorts
        self.memberships = memberships
        self.users = users
        self.notifications = notifications

    def get_assignment(self, assignment_id: int) -> Assignment:
        return self.require(Assignment, assignment_id)

    def assign(self, plan_id: int, data: AssignmentCreate) -> list[Assignment]:
        plan = self.plans.get_plan(plan_id)
        if data.cohort_id is not None:
            cohort = self.cohorts.get_cohort(data.cohort_id)
            if cohort.manager_id != plan.manager_id:
                raise WorkflowError("Plan and cohort must belong to the same manager", 403)
            trainee_ids = self.memberships.trainee_ids(cohort.id)
            if not trainee_ids:
                raise WorkflowError("Cannot assign a plan to an empty cohort")
        else:
            trainee = self.users.require_role(data.trainee_id, Role.trainee)
            trainee_ids = [trainee.id]
        existing = {assignment.trainee_id for assignment in self.repository.for_plan(plan_id)}
        if existing.intersection(trainee_ids):
            raise ConflictError("Plan is already assigned to one or more target trainees")
        assignments = []
        for trainee_id in trainee_ids:
            assignment = self.repository.add(Assignment(
                plan_id=plan_id, trainee_id=trainee_id, cohort_id=data.cohort_id, due_date=data.due_date,
            ))
            assignments.append(assignment)
            self.notifications.notify(trainee_id, f"Training plan assigned: {plan.title}")
        self.repository.save()
        return assignments

    def list_assignments(
        self, trainee_id: int, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None,
    ) -> list[Assignment]:
        self.users.require_role(trainee_id, Role.trainee)
        return self.repository.for_trainee(trainee_id, offset=offset, limit=limit, manager_id=manager_id)