from datetime import datetime

from pydantic import Field

from .base import Input, View


class ReportCreate(Input):
    trainee_id: int = Field(gt=0)
    progress: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1, max_length=10000)


class FeedbackCreate(Input):
    manager_id: int = Field(gt=0)
    feedback: str = Field(min_length=1, max_length=10000)


class ReportView(View):
    id: int
    assignment_id: int
    progress: int
    summary: str
    feedback: str | None
    reviewed_by_id: int | None
    created_at: datetime