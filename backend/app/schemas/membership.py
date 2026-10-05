from pydantic import Field

from .base import Input, View


class MemberCreate(Input):
    trainee_id: int = Field(gt=0)


class MemberView(View):
    cohort_id: int
    trainee_id: int