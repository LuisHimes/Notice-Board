from __future__ import annotations

from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import Base

Model = TypeVar("Model", bound=Base)


class ConflictError(Exception):
    pass


class Repository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, model: type[Model], identifier: int) -> Model | None:
        return self.session.get(model, identifier)

    def list(self, model: type[Model], *, offset: int = 0, limit: int = 100, conditions=(), **filters) -> list[Model]:
        statement = select(model).filter_by(**filters).where(*conditions)
        statement = statement.order_by(*model.__table__.primary_key.columns).offset(offset).limit(limit)
        return list(self.session.scalars(statement))

    def all(self, model: type[Model], **filters) -> list[Model]:
        return list(self.session.scalars(select(model).filter_by(**filters)))

    def add(self, instance: Model) -> Model:
        self.session.add(instance)
        return instance

    def save(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise ConflictError("A record with these unique values already exists") from error