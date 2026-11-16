from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationPage,
    NotificationRead,
    UnreadCountResponse,
)
from app.services.notification_service import mark_all_read, unread_count

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationPage)
def notifications(
    unread_only: bool = False,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationPage:
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="page must be positive and limit must be between 1 and 100.")
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return NotificationPage(
        items=[NotificationRead.model_validate(item) for item in items],
        page=page,
        limit=limit,
        total=total,
    )


@router.patch("/read-all", response_model=MarkAllReadResponse)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> MarkAllReadResponse:
    return MarkAllReadResponse(updated_count=mark_all_read(db, user.id))


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> UnreadCountResponse:
    return UnreadCountResponse(unread_count=unread_count(db, user.id))


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def read_one(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
