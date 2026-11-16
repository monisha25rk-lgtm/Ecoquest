from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    college_id: Mapped[int | None] = mapped_column(ForeignKey("colleges.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    organization_type: Mapped[str] = mapped_column(String(40), nullable=False, default="Other")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    department_affiliation: Mapped[str | None] = mapped_column(String(160), nullable=True)
    supporting_document_original_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supporting_document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    supporting_document_content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    supporting_document_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    events = relationship("Event", back_populates="organization")
    college = relationship("College", back_populates="organizations")
