from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (
        UniqueConstraint("student_id", "event_id", name="uq_event_registration_student_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    registration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REGISTERED")

    student = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
    progress_logs = relationship("ProgressLog", back_populates="registration", cascade="all, delete-orphan")
    submission = relationship("Submission", back_populates="registration", uselist=False, cascade="all, delete-orphan")
