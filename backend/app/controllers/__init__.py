from fastapi import APIRouter

from . import assignment, auth, cohort, membership, notification, plan, progress_report, staff, trainee

router = APIRouter(prefix="/api")
for controller in (auth, staff, trainee, cohort, membership, plan, assignment, progress_report, notification):
    router.include_router(controller.router)

__all__ = ["router"]