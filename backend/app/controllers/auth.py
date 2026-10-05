from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from ..dependencies.auth import Auth, CurrentUser, HRUser, Settings
from ..schemas.auth import PasswordChange, PasswordSet, TokenView
from ..schemas.user import UserView
from ..security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenView)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Auth, settings: Settings, response: Response,
):
    user, credential = service.authenticate(form.username, form.password)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return TokenView(
        access_token=create_access_token(user.id, credential.token_version, settings),
        expires_in=settings.token_minutes * 60,
    )


@router.get("/me", response_model=UserView)
def current_profile(user: CurrentUser):
    return user


@router.put("/accounts/{user_id}/password", status_code=204)
def provision_password(user_id: int, data: PasswordSet, service: Auth, actor: HRUser):
    service.set_password(user_id, data.password.get_secret_value())


@router.post("/password", status_code=204)
def change_password(data: PasswordChange, service: Auth, user: CurrentUser):
    service.change_password(user, data.current_password.get_secret_value(), data.new_password.get_secret_value())


@router.post("/logout", status_code=204)
def logout(service: Auth, user: CurrentUser):
    service.logout(user.id)