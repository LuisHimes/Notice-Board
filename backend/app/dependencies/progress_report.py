from typing import Annotated

from fastapi import Depends

from ..services.progress_report import ProgressReportService
from .assignment import Assignments
from .notification import Notifications
from .plan import Plans
from .repositories import ProgressReportRepositoryDep
from .user import Users


def get_progress_report_service(
    repository: ProgressReportRepositoryDep,
    assignments: Assignments,
    plans: Plans,
    users: Users,
    notifications: Notifications,
) -> ProgressReportService:
    return ProgressReportService(
        repository=repository,
        assignments=assignments,
        plans=plans,
        users=users,
        notifications=notifications,
    )


ProgressReports = Annotated[ProgressReportService, Depends(get_progress_report_service)]