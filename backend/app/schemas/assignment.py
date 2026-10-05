from datetime import datetime

from pydantic import Field, model_validator

from .base import Input, View


class AssignmentCreate(Input):
    trainee_id: int | None = Field(default=None, gt=0)
    cohort_id: int | None = Field(default=None, gt=0)
    due_date: datetime | None = None

    @model_validator(mode="after")
    def require_one_target(self):
        if (self.trainee_id is None) == (self.cohort_id is None):
            raise ValueError("Provide exactly one of trainee_id or cohort_id")
        return self


class AssignmentView(View):
    id: int
    plan_id: int
    trainee_id: int
    cohort_id: int | None
    due_date: datetime | None
    progress: int
    created_at: datetime