from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..repositories.assignment import AssignmentRepository
from ..repositories.cohort import CohortRepository
from ..repositories.membership import MembershipRepository
from ..repositories.notification import NotificationRepository
from ..repositories.plan import PlanRepository
from ..repositories.progress_report import ProgressReportRepository
from ..repositories.user import UserRepository

SessionDep = Annotated[Session, Depends(get_session)]


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_cohort_repository(session: SessionDep) -> CohortRepository:
    return CohortRepository(session)


def get_membership_repository(session: SessionDep) -> MembershipRepository:
    return MembershipRepository(session)


def get_plan_repository(session: SessionDep) -> PlanRepository:
    return PlanRepository(session)


def get_assignment_repository(session: SessionDep) -> AssignmentRepository:
    return AssignmentRepository(session)


def get_progress_report_repository(session: SessionDep) -> ProgressReportRepository:
    return ProgressReportRepository(session)


def get_notification_repository(session: SessionDep) -> NotificationRepository:
    return NotificationRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
CohortRepositoryDep = Annotated[CohortRepository, Depends(get_cohort_repository)]
MembershipRepositoryDep = Annotated[MembershipRepository, Depends(get_membership_repository)]
PlanRepositoryDep = Annotated[PlanRepository, Depends(get_plan_repository)]
AssignmentRepositoryDep = Annotated[AssignmentRepository, Depends(get_assignment_repository)]
ProgressReportRepositoryDep = Annotated[ProgressReportRepository, Depends(get_progress_report_repository)]
NotificationRepositoryDep = Annotated[NotificationRepository, Depends(get_notification_repository)]