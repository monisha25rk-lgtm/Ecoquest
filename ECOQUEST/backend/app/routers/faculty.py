import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.faculty_assignment import FacultyAssignment
from app.models.registration import EventRegistration
from app.models.submission import Submission
from app.models.user import User
from app.schemas.person2 import FacultyAssignmentCreate, FacultyAssignmentRangeCreate, FacultyAssignmentRangeRead, FacultyAssignmentRead, ReviewCreate
from app.services.person2_service import serialize_submission, verify_submission

router = APIRouter(tags=["Faculty"])


def _assignment_read(item: FacultyAssignment) -> dict:
    return {
        "id": item.id, "college_id": item.college_id, "teacher_id": item.teacher_id,
        "teacher_name": item.teacher.full_name, "student_id": item.student_id,
        "student_name": item.student.full_name, "student_usn": item.student_usn,
        "student_department": item.student.department,
        "status": item.status, "assigned_at": item.assigned_at, "updated_at": item.updated_at,
    }


def _admin_scope(query, admin: User, column):
    return query.where(column == admin.college_id) if admin.college_id is not None else query


@router.get("/admin/teachers")
def teachers(db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    query = select(User).where(User.role == "TEACHER", User.is_active.is_(True)).order_by(User.full_name)
    if admin.college_id is not None:
        query = query.where(or_(User.college_id == admin.college_id, User.college_id.is_(None)))
    return [{"id": teacher.id, "full_name": teacher.full_name, "email": teacher.email, "department": teacher.department, "college_id": teacher.college_id} for teacher in db.scalars(query).all()]


@router.get("/admin/students")
def students(db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    query = select(User).where(User.role == "STUDENT", User.is_active.is_(True)).order_by(User.full_name)
    if admin.college_id is not None:
        query = query.where(User.college_id == admin.college_id)
    return [{"id": student.id, "full_name": student.full_name, "email": student.email, "usn": student.usn, "department": student.department, "semester": student.semester, "college_id": student.college_id} for student in db.scalars(query).all()]


@router.get("/admin/faculty-assignments", response_model=list[FacultyAssignmentRead])
def assignments(db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    query = select(FacultyAssignment).options(selectinload(FacultyAssignment.teacher), selectinload(FacultyAssignment.student)).order_by(FacultyAssignment.updated_at.desc())
    if admin.college_id is not None:
        query = query.where(FacultyAssignment.college_id == admin.college_id)
    return [_assignment_read(item) for item in db.scalars(query).all()]


@router.post("/admin/faculty-assignments", response_model=FacultyAssignmentRead)
def assign_student(payload: FacultyAssignmentCreate, db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    teacher = db.get(User, payload.teacher_id)
    student = db.scalar(select(User).where(User.usn == payload.student_usn.upper(), User.role == "STUDENT"))
    if not teacher or teacher.role != "TEACHER" or not student:
        raise HTTPException(404, "Teacher or student was not found.")
    college_id = admin.college_id or student.college_id or teacher.college_id
    if college_id is None or (admin.college_id is not None and college_id != admin.college_id):
        raise HTTPException(403, "The teacher and student must belong to the authorized college.")
    if teacher.college_id is not None and teacher.college_id != college_id:
        raise HTTPException(403, "The teacher is outside the authorized college.")
    if student.college_id is not None and student.college_id != college_id:
        raise HTTPException(403, "The student is outside the authorized college.")
    if teacher.college_id is None:
        teacher.college_id = college_id
    active = db.scalar(select(FacultyAssignment).where(FacultyAssignment.student_id == student.id, FacultyAssignment.status == "ACTIVE"))
    if active and active.teacher_id == teacher.id:
        return _assignment_read(active)
    if active:
        active.status = "INACTIVE"
    assignment = FacultyAssignment(college_id=college_id, teacher_id=teacher.id, student_id=student.id, student_usn=student.usn.upper(), status="ACTIVE")
    db.add(assignment); db.commit(); db.refresh(assignment)
    return _assignment_read(db.scalar(select(FacultyAssignment).options(selectinload(FacultyAssignment.teacher), selectinload(FacultyAssignment.student)).where(FacultyAssignment.id == assignment.id)))


@router.post("/admin/faculty-assignments/range", response_model=FacultyAssignmentRangeRead)
def assign_student_range(payload: FacultyAssignmentRangeCreate, db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    start = payload.start_usn.strip().upper()
    end = payload.end_usn.strip().upper()
    start_match = re.fullmatch(r"(.*?)(\d+)$", start)
    end_match = re.fullmatch(r"(.*?)(\d+)$", end)
    if not start_match or not end_match or start_match.group(1) != end_match.group(1):
        raise HTTPException(422, "Enter a valid USN range with the same prefix, for example 4NI24CS128 to 4NI24CS132.")
    first = int(start_match.group(2))
    last = int(end_match.group(2))
    if last < first:
        raise HTTPException(422, "The ending USN must be greater than or equal to the starting USN.")
    if last - first > 500:
        raise HTTPException(422, "A single assignment range cannot contain more than 501 USNs.")

    teacher = db.get(User, payload.teacher_id)
    if not teacher or teacher.role != "TEACHER":
        raise HTTPException(404, "Teacher was not found.")
    if admin.college_id is not None and teacher.college_id not in (None, admin.college_id):
        raise HTTPException(403, "The teacher is outside the authorized college.")

    prefix = start_match.group(1)
    width = max(len(start_match.group(2)), len(end_match.group(2)))
    requested_usns = [f"{prefix}{number:0{width}d}" for number in range(first, last + 1)]
    students = {student.usn.upper(): student for student in db.scalars(select(User).where(User.role == "STUDENT", User.usn.in_(requested_usns))).all()}
    missing_usns = [student_usn for student_usn in requested_usns if student_usn not in students]
    assignments = []

    for student_usn in requested_usns:
        student = students.get(student_usn)
        if student is None:
            continue
        college_id = admin.college_id or student.college_id or teacher.college_id
        if college_id is None or (admin.college_id is not None and college_id != admin.college_id):
            raise HTTPException(403, f"Student {student_usn} is outside the authorized college.")
        if student.college_id is not None and student.college_id != college_id:
            raise HTTPException(403, f"Student {student_usn} is outside the authorized college.")
        if teacher.college_id is None:
            teacher.college_id = college_id
        active = db.scalar(select(FacultyAssignment).where(FacultyAssignment.student_id == student.id, FacultyAssignment.status == "ACTIVE"))
        if active and active.teacher_id == teacher.id:
            assignments.append(active)
            continue
        if active:
            active.status = "INACTIVE"
        assignment = FacultyAssignment(college_id=college_id, teacher_id=teacher.id, student_id=student.id, student_usn=student_usn, status="ACTIVE")
        db.add(assignment)
        db.flush()
        assignments.append(assignment)

    db.commit()
    assignment_ids = [assignment.id for assignment in assignments]
    loaded = db.scalars(select(FacultyAssignment).options(selectinload(FacultyAssignment.teacher), selectinload(FacultyAssignment.student)).where(FacultyAssignment.id.in_(assignment_ids))).all() if assignment_ids else []
    loaded_by_id = {assignment.id: assignment for assignment in loaded}
    return {"assignments": [_assignment_read(loaded_by_id[assignment_id]) for assignment_id in assignment_ids], "missing_usns": missing_usns, "assigned_count": len(assignment_ids)}


def _teacher_submission_read(submission: Submission) -> dict:
    data = serialize_submission(submission)
    registration = submission.registration
    student = registration.student
    event = registration.event
    latest_review = submission.reviews[-1] if submission.reviews else None
    event_eco_points = event.approved_eco_points if event.approved_eco_points is not None else event.proposed_eco_points
    awarded_eco_points = None
    if latest_review and latest_review.decision == "APPROVED" and latest_review.grade is not None:
        awarded_eco_points = round(event_eco_points * latest_review.grade / 100)
    data.update({
        "student": {"id": student.id, "full_name": student.full_name, "usn": student.usn, "department": student.department, "semester": student.semester},
        "event": {"id": event.id, "title": event.title, "category_id": event.category_id, "start_date": event.start_date, "end_date": event.end_date, "venue": event.venue, "eco_points": event_eco_points},
        "assigned_teacher_id": submission.assigned_teacher_id,
        "version": submission.version,
        "awarded_eco_points": awarded_eco_points,
    })
    return data


@router.get("/teacher/dashboard")
def teacher_dashboard(db: Session = Depends(get_db), teacher: User = Depends(require_role("TEACHER"))):
    assigned = db.scalars(select(FacultyAssignment).options(selectinload(FacultyAssignment.student)).where(FacultyAssignment.teacher_id == teacher.id, FacultyAssignment.status == "ACTIVE").order_by(FacultyAssignment.updated_at.desc())).all()
    submissions = db.scalars(
        select(Submission).join(EventRegistration, Submission.registration_id == EventRegistration.id)
        .join(FacultyAssignment, FacultyAssignment.student_id == EventRegistration.student_id)
        .where(FacultyAssignment.teacher_id == teacher.id, FacultyAssignment.status == "ACTIVE", Submission.assigned_teacher_id == teacher.id)
        .options(selectinload(Submission.files), selectinload(Submission.reviews), selectinload(Submission.registration).selectinload(EventRegistration.student), selectinload(Submission.registration).selectinload(EventRegistration.event))
        .order_by(Submission.updated_at.desc())
    ).all()
    return {"teacher": {"id": teacher.id, "full_name": teacher.full_name}, "assigned_students": [{"id": item.student.id, "full_name": item.student.full_name, "usn": item.student.usn, "department": item.student.department, "semester": item.student.semester} for item in assigned], "submissions": [_teacher_submission_read(item) for item in submissions]}


@router.patch("/teacher/submissions/{submission_id}/review")
def review_teacher_submission(submission_id: int, payload: ReviewCreate, db: Session = Depends(get_db), teacher: User = Depends(require_role("TEACHER"))):
    submission = db.scalar(select(Submission).where(Submission.id == submission_id).options(selectinload(Submission.files), selectinload(Submission.reviews), selectinload(Submission.registration).selectinload(EventRegistration.student), selectinload(Submission.registration).selectinload(EventRegistration.event)))
    if not submission:
        raise HTTPException(404, "Submission not found.")
    if submission.assigned_teacher_id != teacher.id:
        raise HTTPException(403, "This submission is not assigned to you.")
    if payload.decision in {"REJECTED", "CHANGES_REQUESTED"} and not payload.note:
        raise HTTPException(422, "Feedback is required for rejection or correction requests.")
    return _teacher_submission_read(verify_submission(db, submission, teacher, payload))
