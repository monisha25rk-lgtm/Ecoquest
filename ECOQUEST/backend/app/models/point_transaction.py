from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PointTransaction(Base):
    __tablename__ = "point_transactions"
    __table_args__ = (
        CheckConstraint(
            "(transaction_type = 'AWARD' AND points >= 0) OR "
            "(transaction_type = 'REVERSAL' AND points <= 0)",
            name="ck_point_transactions_type_points",
        ),
        CheckConstraint(
            "transaction_type IN ('AWARD', 'REVERSAL')",
            name="ck_point_transactions_type",
        ),
        UniqueConstraint("evaluation_id", "transaction_type", name="uq_point_transactions_evaluation_type"),
        UniqueConstraint("student_id", "event_id", "transaction_type", name="uq_point_transactions_student_event_type"),
        UniqueConstraint("reversal_of", name="uq_point_transactions_reversal_of"),
    )

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False, index=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False, index=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reversal_of: Mapped[int | None] = mapped_column(
        ForeignKey("point_transactions.transaction_id"), nullable=True
    )
