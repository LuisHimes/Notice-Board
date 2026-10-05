from typing import Literal

from pydantic import Field, SecretStr

from .base import Input, View


class PasswordSet(Input):
    password: SecretStr = Field(min_length=12, max_length=128)


class PasswordChange(Input):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


class TokenView(View):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int