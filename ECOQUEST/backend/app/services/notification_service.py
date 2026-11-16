from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.services.event_service import get_events_table

EVENT_PUBLISHED_TITLE = "New event published"


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    event_id: int | None = None,
) -> Notification:
    existing = db.scalar(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.event_id == event_id,
            Notification.title == title,
        )
    )
    if existing is not None:
        return existing
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        event_id=event_id,
    )
    db.add(notification)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.event_id == event_id,
                Notification.title == title,
            )
        )
        if existing is None:
            raise
        return existing
    return notification


def notify_event_published(db: Session, event_id: int, recipient_ids: list[int] | None = None) -> int:
    event_table = get_events_table(db)
    event = db.execute(
        select(event_table).where(
            event_table.c.id == event_id,
            event_table.c.status == "PUBLISHED",
        )
    ).mappings().one_or_none()
    if event is None:
        raise ValueError("Only a published event can generate publication notifications.")
    if recipient_ids is None:
        query = select(User.id).where(User.role == "STUDENT", User.is_active.is_(True))
        if event.get("college_id") is not None:
            query = query.where(User.college_id == event["college_id"])
        recipients = db.scalars(query).all()
    else:
        recipients = db.scalars(
            select(User.id).where(
                User.id.in_(recipient_ids),
                User.role == "STUDENT",
                User.is_active.is_(True),
            )
        ).all()
    created = 0
    title = EVENT_PUBLISHED_TITLE
    message = f"A new event is available: {event['title']}."
    for user_id in recipients:
        already_exists = db.scalar(
            select(Notification.id).where(
                Notification.user_id == user_id,
                Notification.event_id == event_id,
                Notification.title == title,
            )
        )
        if already_exists is None:
            db.add(Notification(user_id=user_id, event_id=event_id, title=title, message=message))
            created += 1
    db.commit()
    return created


def unread_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    ) or 0


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount or 0
