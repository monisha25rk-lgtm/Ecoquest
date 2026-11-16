from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    event_id: int | None
    is_read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationRead]
    page: int
    limit: int
    total: int


class MarkAllReadResponse(BaseModel):
    updated_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
