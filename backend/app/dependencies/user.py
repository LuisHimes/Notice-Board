from typing import Annotated

from fastapi import Depends

from ..services.user import UserService
from .repositories import UserRepositoryDep


def get_user_service(repository: UserRepositoryDep) -> UserService:
    return UserService(repository=repository)


Users = Annotated[UserService, Depends(get_user_service)]