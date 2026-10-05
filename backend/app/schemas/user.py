from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from ..models.user import Role
from .base import Input, View


class UserCreate(Input):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class StaffCreate(UserCreate):
    role: Literal["hr", "manager"]


class TraineeCreate(UserCreate):
    onboarded_by_id: int = Field(gt=0)


class UserView(View):
    id: int
    name: str
    email: str
    role: Role
    onboarded_by_id: int | None
    created_at: datetime