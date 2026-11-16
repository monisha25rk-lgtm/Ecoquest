from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.registration import EventRegistration
from app.models.user import User
from app.schemas.event import EventRead
from app.schemas.registration import RegistrationRead
from app.services.event_service import find_event
from app.services.registration_service import register_student_for_event

router = APIRouter(tags=["Registrations"])


@router.post("/events/{event_id}/register", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_for_event(
    event_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_role("STUDENT")),
) -> RegistrationRead:
    registration = register_student_for_event(db, student, event_id)
    event, _ = find_event(db, event_id)
    return RegistrationRead(
        id=registration.id,
        student_id=registration.student_id,
        event_id=registration.event_id,
        registration_date=registration.registration_date,
        status=registration.status,
        event=EventRead(**event),
    )


@router.get("/registrations/me", response_model=list[RegistrationRead])
def my_registrations(
    db: Session = Depends(get_db),
    student: User = Depends(require_role("STUDENT")),
) -> list[RegistrationRead]:
    registrations = db.scalars(
        select(EventRegistration)
        .where(EventRegistration.student_id == student.id)
        .order_by(EventRegistration.registration_date.desc())
    ).all()
    response = []
    for registration in registrations:
        try:
            event, _ = find_event(db, registration.event_id, published_only=False)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            continue
        response.append(
            RegistrationRead(
                id=registration.id,
                student_id=registration.student_id,
                event_id=registration.event_id,
                registration_date=registration.registration_date,
                status=registration.status,
                event=EventRead(**event),
            )
        )
    return response
