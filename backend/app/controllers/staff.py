from fastapi import APIRouter

from ..dependencies import Users
from ..dependencies.auth import HRUser
from ..schemas.user import StaffCreate, UserView

router = APIRouter(tags=["Onboarding"])


@router.post("/staff", response_model=UserView, status_code=201)
def create_staff(data: StaffCreate, service: Users, actor: HRUser):
    return service.create_staff(data)