import logging
from datetime import date, datetime, time, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import MetaData, Table, func, inspect, or_, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.registration import EventRegistration

logger = logging.getLogger(__name__)
REQUIRED_EVENT_COLUMNS = {
    "id", "title", "category_id", "start_date", "end_date", "venue",
    "registration_deadline", "capacity", "status",
}


def get_events_table(db: Session) -> Table:
    bind = db.get_bind()
    if "events" not in inspect(bind).get_table_names():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event discovery is unavailable until the shared events table is integrated.",
        )
    metadata = Base.metadata if "events" not in Base.metadata.tables else MetaData()
    table = metadata.tables.get("events")
    if table is None:
        table = Table("events", metadata, autoload_with=bind)
    missing = REQUIRED_EVENT_COLUMNS.difference(table.c.keys())
    if missing:
        logger.error("Shared events table is missing required contract columns: %s", sorted(missing))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The shared events schema does not satisfy the EcoQuest event integration contract.",
        )
    return table


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except ValueError:
        return None


def serialize_event(db: Session, row: Any, event_table: Table) -> dict[str, Any]:
    event = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    event_id = event["id"]
    active_count = db.scalar(
        select(func.count(EventRegistration.id)).where(
            EventRegistration.event_id == event_id,
            EventRegistration.status == "REGISTERED",
        )
    ) or 0
    data: dict[str, Any] = {}
    optional_fields = {
        "description", "organization_id", "category_id", "venue", "entry_fee", "facilities",
        "college_id", "event_mode", "approved_by_id",
        "eligibility_requirements", "participation_requirements",
        "evidence_requirements", "poster_path", "approved_eco_points", "proposed_eco_points", "status", "title",
    }
    for field in optional_fields:
        if field in event_table.c:
            data[field] = event.get(field)
    if data.get("poster_path"):
        data["poster_path"] = f"/events/{event_id}/poster"
    data.update(
        id=event_id,
        organization_name=_organization_name(db, event),
        category_name=_category_name(db, event.get("category_id")),
        college_name=_college_name(db, event.get("college_id")),
        review_note=event.get("review_note"),
        start_date=_as_datetime(event.get("start_date")),
        end_date=_as_datetime(event.get("end_date")),
        registration_deadline=_as_datetime(event.get("registration_deadline")),
        capacity=event.get("capacity"),
        available_seats=max(0, event["capacity"] - active_count) if event.get("capacity") is not None else None,
    )
    return data


def _organization_name(db: Session, event: dict[str, Any]) -> str | None:
    organization_id = event.get("organization_id")
    if organization_id is None:
        return None
    bind = db.get_bind()
    if "organizations" not in inspect(bind).get_table_names():
        return None
    organizations = Table("organizations", MetaData(), autoload_with=bind)
    name_column = next((name for name in ("name", "organization_name") if name in organizations.c), None)
    if name_column is None or "id" not in organizations.c:
        return None
    return db.execute(select(organizations.c[name_column]).where(organizations.c.id == organization_id)).scalar_one_or_none()


def _category_name(db: Session, category_id: int | None) -> str | None:
    if category_id is None:
        return None
    from app.models.category import Category

    return db.scalar(select(Category.name).where(Category.id == category_id))


def _college_name(db: Session, college_id: int | None) -> str | None:
    if college_id is None:
        return None
    from app.models.college import College
    return db.scalar(select(College.name).where(College.id == college_id))


def find_event(db: Session, event_id: int, *, published_only: bool = True) -> tuple[dict[str, Any], Table]:
    table = get_events_table(db)
    query = select(table).where(table.c.id == event_id)
    if published_only:
        query = query.where(table.c.status == "PUBLISHED")
    row = db.execute(query).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    return serialize_event(db, row, table), table


def list_events(
    db: Session,
    *,
    search: str | None,
    category_id: int | None,
    event_date: date | None,
    upcoming: bool,
    registration_open: bool,
    college_id: int | None = None,
    page: int,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    table = get_events_table(db)
    query = select(table).where(table.c.status == "PUBLISHED")
    if college_id is not None and "college_id" in table.c:
        query = query.where(table.c.college_id == college_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        search_terms = [table.c.title.ilike(search_pattern)]
        if "organization_id" in table.c and "organizations" in inspect(db.get_bind()).get_table_names():
            organizations = Table("organizations", MetaData(), autoload_with=db.get_bind())
            organization_name = next(
                (name for name in ("name", "organization_name") if name in organizations.c),
                None,
            )
            if organization_name and "id" in organizations.c:
                matching_organization = (
                    select(organizations.c.id)
                    .where(organizations.c[organization_name].ilike(search_pattern))
                    .scalar_subquery()
                )
                search_terms.append(table.c.organization_id == matching_organization)
        query = query.where(or_(*search_terms))
    if category_id is not None:
        query = query.where(table.c.category_id == category_id)
    if event_date is not None:
        query = query.where(func.date(table.c.start_date) == event_date.isoformat())
    if upcoming:
        query = query.where(table.c.start_date >= datetime.now(timezone.utc).replace(tzinfo=None))
    if registration_open:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        query = query.where(table.c.registration_deadline >= now)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(table.c.start_date.asc()).offset((page - 1) * limit).limit(limit)
    ).mappings().all()
    return [serialize_event(db, row, table) for row in rows], total
