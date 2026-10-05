from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Membership(Base):
    __tablename__ = "memberships"

    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), primary_key=True)
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)