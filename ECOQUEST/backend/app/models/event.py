from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(240), nullable=True)
    event_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="IN_PERSON")
    entry_fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    facilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    registration_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligibility_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    participation_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    proposed_eco_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    approved_eco_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    organization = relationship("Organization", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")
    college = relationship("College", back_populates="events")
