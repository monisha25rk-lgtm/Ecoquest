import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.models.faculty_assignment import FacultyAssignment
from app.models.organization import Organization
from app.models.progress import ProgressLog
from app.models.registration import EventRegistration
from app.models.review import Review
from app.models.submission import Submission, SubmissionFile
from app.models.user import User
from app.services.notification_service import notify_event_published
from app.services.points_service import allocate_points_for_evaluation

UPLOAD_ROOT = Path(os.getenv("ECOQUEST_UPLOAD_DIR", Path(__file__).resolve().parents[2] / "uploads"))
ALLOWED_TYPES = {
    "image/jpeg": "PHOTO", "image/png": "PHOTO", "image/webp": "PHOTO",
    "application/pdf": "REPORT", "application/msword": "REPORT",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "REPORT",
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ORGANIZATION_DOCUMENT_BYTES = 10 * 1024 * 1024
ORGANIZATION_DOCUMENT_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/webp",
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def register_organization(db: Session, user: User, payload) -> Organization:
    if db.scalar(select(Organization.id).where(Organization.owner_id == user.id)) is not None:
        raise ValueError("You already have an organization registration.")
    if db.scalar(select(Organization.id).where(Organization.name == payload.organization_name.strip())) is not None:
        raise ValueError("An organization with this name already exists.")
    organization = Organization(
        owner_id=user.id,
        college_id=user.college_id,
        name=payload.organization_name.strip(),
        organization_type=payload.organization_type,
        description=payload.description.strip(),
        contact_email=str(payload.official_email).lower(),
        contact_phone=payload.contact_number.strip(),
        department_affiliation=payload.department_affiliation.strip() if payload.department_affiliation else None,
        status="PENDING",
    )
    db.add(organization); db.commit(); db.refresh(organization)
    return organization


async def read_organization_document(upload: UploadFile) -> dict:
    if upload.content_type not in ORGANIZATION_DOCUMENT_TYPES:
        raise HTTPException(415, "Supporting document must be a PDF, JPG, PNG, WEBP, DOC or DOCX file.")
    data = await upload.read(MAX_ORGANIZATION_DOCUMENT_BYTES + 1)
    if len(data) > MAX_ORGANIZATION_DOCUMENT_BYTES:
        raise HTTPException(413, "Supporting document must be 10 MB or smaller.")
    original_name = Path(upload.filename or "supporting-document").name
    suffix = Path(original_name).suffix.lower()
    suffix = re.sub(r"[^a-z0-9.]", "", suffix)[:10]
    return {"data": data, "original_name": original_name[:255], "suffix": suffix, "content_type": upload.content_type}


def save_organization_document(organization: Organization, document: dict) -> None:
    stored_name = f"{uuid.uuid4().hex}{document['suffix']}"
    folder = UPLOAD_ROOT / "organizations" / str(organization.id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / stored_name).write_bytes(document["data"])
    organization.supporting_document_original_name = document["original_name"]
    organization.supporting_document_path = f"organizations/{organization.id}/{stored_name}"
    organization.supporting_document_content_type = document["content_type"]
    organization.supporting_document_size_bytes = len(document["data"])


def organization_for_owner(db: Session, user: User) -> Organization:
    organization = db.scalar(select(Organization).where(Organization.owner_id == user.id))
    if not organization:
        raise HTTPException(404, "Organization profile not found.")
    return organization


def validate_event(payload, category_exists: bool) -> None:
    now = datetime.now(timezone.utc)
    if not category_exists: raise HTTPException(422, "Selected category does not exist.")
    start_date = payload.start_date.replace(tzinfo=timezone.utc) if payload.start_date.tzinfo is None else payload.start_date.astimezone(timezone.utc)
    end_date = payload.end_date.replace(tzinfo=timezone.utc) if payload.end_date.tzinfo is None else payload.end_date.astimezone(timezone.utc)
    registration_deadline = payload.registration_deadline.replace(tzinfo=timezone.utc) if payload.registration_deadline.tzinfo is None else payload.registration_deadline.astimezone(timezone.utc)
    if end_date <= start_date: raise HTTPException(422, "End date must be after start date.")
    if registration_deadline >= start_date: raise HTTPException(422, "Registration deadline must be before the event starts.")
    if start_date <= now: raise HTTPException(422, "Event start date must be in the future.")


def serialize_submission(submission: Submission) -> dict:
    return {"id": submission.id, "registration_id": submission.registration_id, "status": submission.status,
            "participation_dates": submission.participation_dates, "student_note": submission.student_note,
            "submitted_at": submission.submitted_at,
            "files": [{"id": f.id, "original_name": f.original_name, "content_type": f.content_type, "file_kind": f.file_kind, "size_bytes": f.size_bytes} for f in submission.files],
            "reviews": [{"id": r.id, "reviewer_id": r.reviewer_id, "decision": r.decision, "grade": r.grade, "note": r.note, "created_at": r.created_at} for r in submission.reviews]}


def ensure_submission(db: Session, registration: EventRegistration, *, note: str | None = None) -> Submission:
    assignment = db.scalar(select(FacultyAssignment).where(FacultyAssignment.student_id == registration.student_id, FacultyAssignment.status == "ACTIVE"))
    submission = db.scalar(select(Submission).where(Submission.registration_id == registration.id).options(selectinload(Submission.files), selectinload(Submission.reviews)))
    if submission is None:
        submission = Submission(registration_id=registration.id, status="DRAFT", student_note=note, assigned_teacher_id=assignment.teacher_id if assignment else None)
        db.add(submission); db.flush()
    elif submission.status == "APPROVED":
        raise HTTPException(409, "Approved submissions cannot be edited.")
    else:
        if submission.status == "CHANGES_REQUESTED":
            submission.version += 1
        submission.assigned_teacher_id = assignment.teacher_id if assignment else submission.assigned_teacher_id
        if note is not None: submission.student_note = note
    return submission


async def save_upload(submission: Submission, upload: UploadFile) -> SubmissionFile:
    if upload.content_type not in ALLOWED_TYPES: raise HTTPException(415, "Only JPG, PNG, WEBP, DOC, DOCX and PDF evidence is allowed.")
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES: raise HTTPException(413, "Each evidence file must be 10 MB or smaller.")
    safe_name = Path(upload.filename or "evidence").name
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    folder = UPLOAD_ROOT / "submissions" / str(submission.id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / stored_name).write_bytes(data)
    return SubmissionFile(submission_id=submission.id, original_name=safe_name, stored_name=stored_name,
                          content_type=upload.content_type, file_kind=ALLOWED_TYPES[upload.content_type], size_bytes=len(data))


def publish_event(db: Session, event: Event, decision, reviewer: User) -> Event:
    if decision.status == "PUBLISHED":
        event.status = "PUBLISHED"; event.approved_eco_points = decision.approved_eco_points if decision.approved_eco_points is not None else event.proposed_eco_points
        event.approved_by_id = reviewer.id
    else: event.status = "REJECTED"; event.approved_eco_points = None
    event.review_note = decision.review_note; event.reviewed_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(event)
    if event.status == "PUBLISHED": notify_event_published(db, event.id)
    return event


def verify_submission(db: Session, submission: Submission, reviewer: User, decision) -> Submission:
    if submission.status == "APPROVED":
        if decision.decision != "APPROVED":
            raise HTTPException(409, "Approved submissions cannot be changed.")
        existing_review = db.scalar(
            select(Review)
            .where(
                Review.submission_id == submission.id,
                Review.submission_version == submission.version,
                Review.decision == "APPROVED",
            )
            .order_by(Review.id.desc())
        )
        if existing_review is not None:
            trigger_reward_allocation(db, submission.registration_id, existing_review.id)
            return submission
    elif submission.status != "PENDING":
        raise HTTPException(409, "Only pending evidence can be evaluated.")

    submission.status = decision.decision
    if decision.decision == "APPROVED" and decision.grade is None:
        raise HTTPException(422, "A grade is required when approving evidence.")
    review = Review(submission_id=submission.id, reviewer_id=reviewer.id, decision=decision.decision, grade=decision.grade, note=decision.note, submission_version=submission.version)
    db.add(review)
    db.flush()
    db.commit()
    db.refresh(submission)
    if decision.decision == "APPROVED":
        trigger_reward_allocation(db, submission.registration_id, review.id)
    return submission


REWARD_ALLOCATOR: Callable[..., object] | None = allocate_points_for_evaluation


def set_reward_allocator(allocator: Callable[..., object] | None) -> None:
    """Allow an integrated reward service to replace the default points allocator."""
    global REWARD_ALLOCATOR
    REWARD_ALLOCATOR = allocator


def trigger_reward_allocation(db: Session, registration_id: int, evaluation_id: int) -> object:
    if REWARD_ALLOCATOR is None:
        raise RuntimeError("The Eco Points reward allocator is not configured.")
    return REWARD_ALLOCATOR(db=db, registration_id=registration_id, evaluation_id=evaluation_id)
