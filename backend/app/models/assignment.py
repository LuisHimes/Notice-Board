from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .common import utc_now


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("plan_id", "trainee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    trainee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cohort_id: Mapped[int | None] = mapped_column(ForeignKey("cohorts.id"))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    progress: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)