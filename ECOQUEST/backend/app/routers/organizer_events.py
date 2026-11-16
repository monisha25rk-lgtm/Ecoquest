from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.category import Category
from app.models.event import Event
from app.models.organization import Organization
from app.models.user import User
from app.schemas.event import EventRead
from app.schemas.organization import OrganizationRead
from app.schemas.person2 import EventCreate, EventDecision
from app.services.event_service import serialize_event
from app.services.person2_service import organization_for_owner, publish_event, validate_event

router = APIRouter(tags=["Organizer Events"])

@router.post("/organizer/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), user: User = Depends(require_role("ORGANIZER"))):
    organization = organization_for_owner(db, user)
    if organization.status != "APPROVED": raise HTTPException(403, "Your organization must be approved before submitting events.")
    validate_event(payload, db.get(Category, payload.category_id) is not None)
    event = Event(organization_id=organization.id, college_id=organization.college_id, **payload.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return EventRead(**serialize_event(db, db.execute(select(Event.__table__).where(Event.id == event.id)).mappings().one(), Event.__table__))

@router.post("/organizer/events/{event_id}/poster", response_model=EventRead)
async def upload_poster(event_id: int, poster: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(require_role("ORGANIZER"))):
    organization = organization_for_owner(db, user); event = db.get(Event, event_id)
    if not event or event.organization_id != organization.id: raise HTTPException(404, "Event not found.")
    if poster.content_type not in {"image/jpeg", "image/png", "image/webp", "application/pdf"}: raise HTTPException(415, "Poster must be an image or PDF.")
    data = await poster.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024: raise HTTPException(413, "Poster must be 5 MB or smaller.")
    from app.services.person2_service import UPLOAD_ROOT
    folder = UPLOAD_ROOT / "posters"; folder.mkdir(parents=True, exist_ok=True)
    name = f"{event.id}_{poster.filename or 'poster'}"; (folder / name).write_bytes(data)
    event.poster_path = f"posters/{name}"; db.commit(); db.refresh(event)
    return EventRead(**serialize_event(db, db.execute(select(Event.__table__).where(Event.id == event.id)).mappings().one(), Event.__table__))

@router.get("/organizer/events", response_model=list[EventRead])
def my_events(db: Session = Depends(get_db), user: User = Depends(require_role("ORGANIZER"))):
    organization = organization_for_owner(db, user)
    return [EventRead(**serialize_event(db, db.execute(select(Event.__table__).where(Event.id == e.id)).mappings().one(), Event.__table__)) for e in db.scalars(select(Event).where(Event.organization_id == organization.id).order_by(Event.created_at.desc())).all()]

@router.get("/admin/events", response_model=list[EventRead])
def admin_events(db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    query = select(Event).order_by(Event.created_at.desc())
    if admin.college_id is not None:
        query = query.where(Event.college_id == admin.college_id)
    return [EventRead(**serialize_event(db, db.execute(select(Event.__table__).where(Event.id == e.id)).mappings().one(), Event.__table__)) for e in db.scalars(query).all()]

@router.patch("/admin/events/{event_id}/decision", response_model=EventRead)
def event_decision(event_id: int, payload: EventDecision, db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    event = db.get(Event, event_id)
    if not event: raise HTTPException(404, "Event not found.")
    if admin.college_id is not None and event.college_id not in (None, admin.college_id):
        raise HTTPException(403, "This event is outside your authorized college.")
    publish_event(db, event, payload, admin)
    return EventRead(**serialize_event(db, db.execute(select(Event.__table__).where(Event.id == event.id)).mappings().one(), Event.__table__))
