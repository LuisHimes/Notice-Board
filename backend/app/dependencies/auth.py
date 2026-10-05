from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from ..models.user import Role, User
from ..repositories.auth import AuthRepository
from ..security import AuthSettings, decode_access_token
from ..services.auth import AuthenticationError, AuthService
from ..services.base import WorkflowError
from .repositories import SessionDep, UserRepositoryDep

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def get_auth_repository(session: SessionDep) -> AuthRepository:
    return AuthRepository(session)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    users: UserRepositoryDep,
) -> AuthService:
    return AuthService(repository=repository, users=users)


Auth = Annotated[AuthService, Depends(get_auth_service)]


def get_auth_settings(request: Request) -> AuthSettings:
    if request.app.state.auth_settings is None:
        request.app.state.auth_settings = AuthSettings.from_env()
    return request.app.state.auth_settings


Settings = Annotated[AuthSettings, Depends(get_auth_settings)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], service: Auth, settings: Settings,
) -> User:
    try:
        user_id, version = decode_access_token(token, settings)
    except jwt.InvalidTokenError as error:
        raise AuthenticationError() from error
    return service.current_user(user_id, version)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_hr(user: CurrentUser) -> User:
    if user.role != Role.hr.value:
        raise WorkflowError("HR role required", 403)
    return user


def require_manager(user: CurrentUser) -> User:
    if user.role != Role.manager.value:
        raise WorkflowError("Manager role required", 403)
    return user


def require_trainee(user: CurrentUser) -> User:
    if user.role != Role.trainee.value:
        raise WorkflowError("Trainee role required", 403)
    return user


def require_staff(user: CurrentUser) -> User:
    if user.role not in (Role.hr.value, Role.manager.value):
        raise WorkflowError("Staff role required", 403)
    return user


HRUser = Annotated[User, Depends(require_hr)]
ManagerUser = Annotated[User, Depends(require_manager)]
TraineeUser = Annotated[User, Depends(require_trainee)]
StaffUser = Annotated[User, Depends(require_staff)]