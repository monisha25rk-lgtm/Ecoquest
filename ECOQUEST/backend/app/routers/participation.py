from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.faculty_assignment import FacultyAssignment
from app.models.progress import ProgressLog
from app.models.registration import EventRegistration
from app.models.submission import Submission, SubmissionFile
from app.models.user import User
from app.schemas.person2 import ProgressCreate, ProgressRead, ReviewCreate, SubmissionRead
from app.services.person2_service import UPLOAD_ROOT, ensure_submission, save_upload, serialize_submission, verify_submission

router = APIRouter(tags=["Participation"])

def student_registration(db, registration_id, user):
    r = db.scalar(select(EventRegistration).where(EventRegistration.id == registration_id, EventRegistration.student_id == user.id))
    if not r: raise HTTPException(404, "Registered activity not found.")
    return r

@router.post("/registrations/{registration_id}/progress", response_model=ProgressRead)
def progress(registration_id: int, payload: ProgressCreate, db: Session = Depends(get_db), user: User = Depends(require_role("STUDENT"))):
    registration = student_registration(db, registration_id, user)
    item = ProgressLog(registration_id=registration.id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.get("/registrations/{registration_id}/submission", response_model=SubmissionRead)
def get_submission(registration_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("STUDENT"))):
    registration = student_registration(db, registration_id, user); submission = db.scalar(select(Submission).where(Submission.registration_id == registration.id).options(selectinload(Submission.files), selectinload(Submission.reviews)))
    if not submission: raise HTTPException(404, "No evidence submission exists yet.")
    return serialize_submission(submission)

@router.post("/registrations/{registration_id}/submission", response_model=SubmissionRead)
async def submit_evidence(registration_id: int, participation_dates: str = Form(...), student_note: str | None = Form(None), files: list[UploadFile] = File(default=[]), db: Session = Depends(get_db), user: User = Depends(require_role("STUDENT"))):
    registration = student_registration(db, registration_id, user)
    existing_submission = db.scalar(select(Submission).where(Submission.registration_id == registration.id).options(selectinload(Submission.files)))
    if existing_submission and existing_submission.status in {"PENDING", "APPROVED"}:
        raise HTTPException(409, "This evidence is already under evaluation or approved.")
    if not files and not (existing_submission and existing_submission.files):
        raise HTTPException(422, "Upload at least one photograph, report or certificate.")
    submission = ensure_submission(db, registration, note=student_note)
    submission.participation_dates = participation_dates; submission.status = "PENDING"
    submission.submitted_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    for upload in files:
        db.add(await save_upload(submission, upload))
    db.commit(); db.refresh(submission)
    submission = db.scalar(select(Submission).where(Submission.id == submission.id).options(selectinload(Submission.files), selectinload(Submission.reviews)))
    return serialize_submission(submission)

@router.get("/admin/submissions", response_model=list[SubmissionRead])
def pending_submissions(db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    items = db.scalars(select(Submission).where(Submission.status.in_(["PENDING", "CHANGES_REQUESTED"])).options(selectinload(Submission.files), selectinload(Submission.reviews)).order_by(Submission.updated_at.desc())).all()
    return [serialize_submission(item) for item in items]

@router.get("/submissions/files/{file_id}")
def download_evidence(file_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("STUDENT", "TEACHER", "ADMIN"))):
    evidence = db.scalar(select(SubmissionFile).where(SubmissionFile.id == file_id))
    if not evidence: raise HTTPException(404, "Evidence file not found.")
    submission = db.get(Submission, evidence.submission_id)
    if user.role == "STUDENT" and (not submission or submission.registration.student_id != user.id): raise HTTPException(403, "You cannot access this evidence file.")
    if user.role == "TEACHER" and (not submission or submission.assigned_teacher_id != user.id): raise HTTPException(403, "You cannot access this evidence file.")
    path = UPLOAD_ROOT / "submissions" / str(evidence.submission_id) / evidence.stored_name
    if not path.is_file(): raise HTTPException(404, "Evidence file is unavailable.")
    return FileResponse(path, media_type=evidence.content_type, filename=evidence.original_name)

@router.patch("/admin/submissions/{submission_id}/review", response_model=SubmissionRead)
def review_submission(submission_id: int, payload: ReviewCreate, db: Session = Depends(get_db), teacher: User = Depends(require_role("TEACHER"))):
    submission = db.scalar(select(Submission).where(Submission.id == submission_id).options(selectinload(Submission.files), selectinload(Submission.reviews)))
    if not submission: raise HTTPException(404, "Submission not found.")
    if submission.assigned_teacher_id != teacher.id:
        raise HTTPException(403, "This submission is not assigned to you.")
    if payload.decision in {"REJECTED", "CHANGES_REQUESTED"} and not payload.note:
        raise HTTPException(422, "Feedback is required for rejection or correction requests.")
    return serialize_submission(verify_submission(db, submission, teacher, payload))
