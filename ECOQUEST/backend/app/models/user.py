from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_usn", "usn", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    usn: Mapped[str] = mapped_column(String(32), nullable=False)
    department: Mapped[str] = mapped_column(String(120), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="STUDENT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    registrations = relationship("EventRegistration", back_populates="student")
    notifications = relationship("Notification", back_populates="user")
    college = relationship("College", back_populates="users", foreign_keys=[college_id])
    faculty_assignments_as_teacher = relationship("FacultyAssignment", foreign_keys="FacultyAssignment.teacher_id", back_populates="teacher")
    faculty_assignments_as_student = relationship("FacultyAssignment", foreign_keys="FacultyAssignment.student_id", back_populates="student")
