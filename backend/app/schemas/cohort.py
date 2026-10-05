from pydantic import Field

from .base import Input, View


class CohortCreate(Input):
    name: str = Field(min_length=1, max_length=120)
    manager_id: int = Field(gt=0)


class CohortView(View):
    id: int
    name: str
    manager_id: int