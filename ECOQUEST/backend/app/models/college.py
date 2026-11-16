from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(40), nullable=True, unique=True)
    official_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", use_alter=True, name="fk_colleges_admin_user"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    users = relationship("User", back_populates="college", foreign_keys="User.college_id")
    organizations = relationship("Organization", back_populates="college")
    events = relationship("Event", back_populates="college")
    assignments = relationship("FacultyAssignment", back_populates="college")
