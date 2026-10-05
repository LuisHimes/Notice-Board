from ..models.credential import Credential
from .base import Repository


class AuthRepository(Repository):
    def credential_for(self, user_id: int) -> Credential | None:
        return self.get(Credential, user_id)