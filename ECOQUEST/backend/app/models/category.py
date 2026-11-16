from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

CATEGORY_NAMES = (
    "Tourism promotion innovation approaches.",
    "To skill rural population.",
    "To assist the marketing of rural produce.",
    "Spreading public awareness under rural outreach programmes.",
    "Setting of the information imparting club for women leading to contribution in social and economic issues.",
    "Reduction in energy consumption.",
    "Promotion of appropriate technologies.",
    "Preparing an actionable business proposal for enhancing the village income.",
    "Helping local schools to achieve good results and enhance their enrolment in higher/technical/vocational education.",
    "Food preservation/Packaging.",
    "Facilitating 100% digitized money transactions.",
    "Developing sustainable water management system.",
    "Developing and managing efficient garbage disposable system.",
    "Contribution to any national-level initiative of Government of India.",
    "Automation of local activities.",
)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def seed_categories(session_factory) -> None:
    with session_factory() as db:
        existing = set(db.query(Category.name).all())
        existing_names = {row[0] for row in existing}
        db.add_all(Category(name=name) for name in CATEGORY_NAMES if name not in existing_names)
        db.commit()
