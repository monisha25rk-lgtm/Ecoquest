from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.registration import EventRegistration
from app.models.user import User
from app.services.event_service import find_event
from app.services.notification_service import create_notification


def register_student_for_event(db: Session, student: User, event_id: int) -> EventRegistration:
    # SQLite serializes writers after BEGIN IMMEDIATE so the seat check and insert are atomic.
    db.rollback()
    if db.get_bind().dialect.name == "sqlite":
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    try:
        event, table = find_event(db, event_id)
        if student.college_id is not None and event.get("college_id") not in (None, student.college_id):
            raise HTTPException(status_code=404, detail="Event not found.")
        now = datetime.now(timezone.utc)
        deadline = event.get("registration_deadline")
        if deadline is not None and deadline <= now:
            raise HTTPException(status_code=409, detail="The registration deadline has passed.")
        existing = db.scalar(
            select(EventRegistration).where(
                EventRegistration.student_id == student.id,
                EventRegistration.event_id == event_id,
            )
        )
        if existing is not None and existing.status != "CANCELLED":
            raise HTTPException(status_code=409, detail="You are already registered for this event.")
        active_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.status == "REGISTERED",
            )
        ) or 0
        capacity = event.get("capacity")
        if capacity is not None and active_count >= capacity:
            raise HTTPException(status_code=409, detail="This event has reached capacity.")
        if existing is None:
            registration = EventRegistration(
                student_id=student.id,
                event_id=event_id,
                status="REGISTERED",
            )
            db.add(registration)
        else:
            existing.status = "REGISTERED"
            existing.registration_date = now.replace(tzinfo=None)
            registration = existing
        create_notification(
            db,
            user_id=student.id,
            title="Event registration confirmed",
            message=f"Your registration for {event['title']} is confirmed.",
            event_id=event_id,
        )
        db.commit()
        db.refresh(registration)
        return registration
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="You are already registered for this event.") from exc
    except Exception:
        db.rollback()
        raise
