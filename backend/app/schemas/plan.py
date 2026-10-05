from pydantic import Field, model_validator

from .base import Input, View


class PlanCreate(Input):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    manager_id: int = Field(gt=0)


class PlanUpdate(Input):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)

    @model_validator(mode="after")
    def require_changes(self):
        if not self.model_fields_set or any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Provide at least one non-null plan field")
        return self


class PlanView(View):
    id: int
    title: str
    description: str
    manager_id: int