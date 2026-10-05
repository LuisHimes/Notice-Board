import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models.user import Role, User
from app.repositories.auth import AuthRepository
from app.repositories.user import UserRepository
from app.schemas.auth import PasswordSet
from app.schemas.user import StaffCreate
from app.services.auth import AuthService
from app.services.base import WorkflowError


def bootstrap_hr(name: str, email: str, password: str, session: Session) -> User:
    data = StaffCreate(name=name, email=email, role="hr")
    secret = PasswordSet(password=password)
    users = UserRepository(session)
    credentials = AuthRepository(session)
    user = users.find_by_email(data.email)
    if user is not None:
        if user.role != Role.hr.value or credentials.credential_for(user.id) is not None:
            raise WorkflowError("Account already exists; bootstrap cannot change its role or reset its password", 409)
    else:
        user = users.add(User(**data.model_dump()))
        session.flush()
    AuthService(credentials, users).set_password(user.id, secret.password.get_secret_value())
    return user


def main() -> None:
    parser = argparse.ArgumentParser(description="Create initial HR credentials without public registration")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Initial HR password (12-128 characters): ")
    if password != getpass("Confirm password: "):
        parser.error("Passwords do not match")
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            user = bootstrap_hr(args.name, args.email, password, session)
            print(f"HR account ready: {user.email}")
    except ValidationError:
        parser.error("Provide a valid name/email and a password containing 12-128 characters")
    except WorkflowError as error:
        parser.error(error.message)


if __name__ == "__main__":
    main()