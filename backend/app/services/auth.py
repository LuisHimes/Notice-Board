from ..models.credential import Credential
from ..models.user import User
from ..repositories.auth import AuthRepository
from ..repositories.user import UserRepository
from ..security import hash_password, password_hasher, verify_password
from .base import BaseService, WorkflowError

dummy_password_hash = hash_password("dummy-account-never-used-for-login")


class AuthenticationError(WorkflowError):
    def __init__(self):
        super().__init__("Invalid credentials or access token", 401)


class AuthService(BaseService[AuthRepository]):
    def __init__(self, repository: AuthRepository, users: UserRepository):
        super().__init__(repository)
        self.users = users

    def authenticate(self, email: str, password: str) -> tuple[User, Credential]:
        if len(email) > 254 or len(password) > 128:
            raise AuthenticationError()
        user = self.users.find_by_email(email.strip().lower())
        credential = self.repository.credential_for(user.id) if user is not None else None
        password_hash = credential.password_hash if credential is not None else dummy_password_hash
        valid = verify_password(password, password_hash)
        if not valid or user is None or credential is None:
            raise AuthenticationError()
        if password_hasher.check_needs_rehash(credential.password_hash):
            credential.password_hash = hash_password(password)
            self.repository.save()
        return user, credential

    def current_user(self, user_id: int, token_version: int) -> User:
        user = self.users.get(User, user_id)
        credential = self.repository.credential_for(user_id)
        if user is None or credential is None or credential.token_version != token_version:
            raise AuthenticationError()
        return user

    def set_password(self, user_id: int, password: str) -> None:
        if self.users.get(User, user_id) is None:
            raise WorkflowError("User not found", 404)
        credential = self.repository.credential_for(user_id)
        password_hash = hash_password(password)
        if credential is None:
            self.repository.add(Credential(user_id=user_id, password_hash=password_hash))
        else:
            credential.password_hash = password_hash
            credential.token_version += 1
        self.repository.save()

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        self.authenticate(user.email, current_password)
        self.set_password(user.id, new_password)

    def logout(self, user_id: int) -> None:
        credential = self.repository.credential_for(user_id)
        if credential is None:
            raise AuthenticationError()
        credential.token_version += 1
        self.repository.save()