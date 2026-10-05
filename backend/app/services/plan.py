from ..models.plan import Plan
from ..models.user import Role
from ..repositories.assignment import AssignmentRepository
from ..repositories.plan import PlanRepository
from ..schemas.plan import PlanCreate, PlanUpdate
from .base import BaseService
from .notification import NotificationService
from .user import UserService


class PlanService(BaseService[PlanRepository]):
    def __init__(
        self, repository: PlanRepository, users: UserService,
        assignments: AssignmentRepository, notifications: NotificationService,
    ):
        super().__init__(repository)
        self.users = users
        self.assignments = assignments
        self.notifications = notifications

    def get_plan(self, plan_id: int) -> Plan:
        return self.require(Plan, plan_id)

    def create_plan(self, data: PlanCreate) -> Plan:
        self.users.require_role(data.manager_id, Role.manager)
        plan = self.repository.add(Plan(**data.model_dump()))
        self.repository.save()
        return plan

    def list_plans(
        self, *, offset: int = 0, limit: int = 100,
        manager_id: int | None = None, trainee_id: int | None = None,
    ) -> list[Plan]:
        return self.repository.list_plans(
            offset=offset, limit=limit, manager_id=manager_id, trainee_id=trainee_id,
        )

    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        plan = self.get_plan(plan_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        for assignment in self.assignments.for_plan(plan_id):
            self.notifications.notify(assignment.trainee_id, f"Training plan updated: {plan.title}")
        self.repository.save()
        return plan