from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_optional_current_user
from app.models.user import User
from app.schemas.event import EventPage, EventRead
from app.services.event_service import find_event, list_events
from app.services.person2_service import UPLOAD_ROOT
from app.models.event import Event

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventPage)
def events(
    search: str | None = Query(default=None, max_length=200),
    category_id: int | None = Query(default=None, ge=1),
    event_date: date | None = Query(default=None, alias="date"),
    upcoming: bool = False,
    registration_open: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
    student: User | None = Depends(get_optional_current_user),
) -> EventPage:
    items, total = list_events(
        db,
        search=search,
        category_id=category_id,
        event_date=event_date,
        upcoming=upcoming,
        registration_open=registration_open,
        college_id=student.college_id if student and student.role == "STUDENT" else None,
        page=page,
        limit=limit,
    )
    return EventPage(items=[EventRead(**item) for item in items], page=page, limit=limit, total=total)


@router.get("/{event_id}", response_model=EventRead)
def event_details(event_id: int, db: Session = Depends(get_db), student: User | None = Depends(get_optional_current_user)) -> EventRead:
    event, _ = find_event(db, event_id)
    if student and student.role == "STUDENT" and student.college_id is not None and event.get("college_id") not in (None, student.college_id):
        raise HTTPException(404, "Event not found.")
    return EventRead(**event)


@router.get("/{event_id}/poster")
def event_poster(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if event is None or event.status != "PUBLISHED" or not event.poster_path:
        raise HTTPException(404, "Event poster not found.")
    path = UPLOAD_ROOT / event.poster_path
    if not path.is_file():
        raise HTTPException(404, "Event poster is unavailable.")
    media_type = "application/pdf" if path.suffix.lower() == ".pdf" else None
    return FileResponse(path, media_type=media_type, filename=path.name)
