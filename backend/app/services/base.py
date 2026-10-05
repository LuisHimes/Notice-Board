from typing import Generic, TypeVar

from ..repositories.base import Model, Repository

RepositoryType = TypeVar("RepositoryType", bound=Repository)


class WorkflowError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BaseService(Generic[RepositoryType]):
    def __init__(self, repository: RepositoryType):
        self.repository = repository

    def require(self, model: type[Model], identifier: int) -> Model:
        instance = self.repository.get(model, identifier)
        if instance is None:
            raise WorkflowError(f"{model.__name__} not found", 404)
        return instance