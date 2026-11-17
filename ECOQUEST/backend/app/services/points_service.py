from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.point_transaction import PointTransaction
from app.models.registration import EventRegistration
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User


def allocate_points_for_evaluation(
    *,
    db: Session,
    registration_id: int,
    evaluation_id: int,
) -> PointTransaction:
    review = db.get(Review, evaluation_id)
    if review is None:
        raise HTTPException(404, "Faculty evaluation not found.")
    if review.decision != "APPROVED" or review.grade is None:
        raise HTTPException(409, "Points can only be allocated for an approved, graded evaluation.")

    submission = db.get(Submission, review.submission_id)
    if submission is None or submission.status != "APPROVED":
        raise HTTPException(409, "Evidence must be approved before points can be allocated.")
    if submission.assigned_teacher_id != review.reviewer_id:
        raise HTTPException(409, "The evaluation must be made by the assigned faculty member.")
    reviewer = db.get(User, review.reviewer_id)
    if reviewer is None or reviewer.role != "TEACHER":
        raise HTTPException(409, "Only an assigned faculty evaluation can award points.")

    registration = db.get(EventRegistration, submission.registration_id)
    if registration is None or registration.id != registration_id:
        raise HTTPException(409, "The evaluation does not match the approved registration.")
    event = db.get(Event, registration.event_id)
    if event is None or event.status not in {"PUBLISHED", "CLOSED"}:
        raise HTTPException(409, "Points can only be allocated for an approved event.")

    existing = db.scalar(
        select(PointTransaction).where(
            PointTransaction.evaluation_id == evaluation_id,
            PointTransaction.transaction_type == "AWARD",
        )
    )
    if existing is not None:
        return existing
    existing = db.scalar(
        select(PointTransaction).where(
            PointTransaction.student_id == registration.student_id,
            PointTransaction.event_id == registration.event_id,
            PointTransaction.transaction_type == "AWARD",
        )
    )
    if existing is not None:
        return existing

    base_points = event.approved_eco_points
    if base_points is None:
        base_points = event.proposed_eco_points
    awarded_points = round(base_points * review.grade / 100)
    transaction = PointTransaction(
        student_id=registration.student_id,
        event_id=registration.event_id,
        evaluation_id=evaluation_id,
        points=awarded_points,
        transaction_type="AWARD",
    )
    db.add(transaction)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(PointTransaction).where(
                PointTransaction.student_id == registration.student_id,
                PointTransaction.event_id == registration.event_id,
                PointTransaction.transaction_type == "AWARD",
            )
        )
        if existing is None:
            raise
        return existing
    db.refresh(transaction)
    return transaction


def reverse_point_transaction(
    db: Session,
    transaction_id: int,
    actor: User,
) -> PointTransaction:
    original = db.get(PointTransaction, transaction_id)
    if original is None:
        raise HTTPException(404, "Point transaction not found.")
    if original.transaction_type != "AWARD":
        raise HTTPException(409, "Only an awarded transaction can be reversed.")

    review = db.get(Review, original.evaluation_id)
    student = db.get(User, original.student_id)
    if review is None or student is None:
        raise HTTPException(409, "The point transaction is missing its evaluation or student.")
    if actor.role == "TEACHER" and review.reviewer_id != actor.id:
        raise HTTPException(403, "Only the faculty member who approved this evaluation can reverse it.")
    if actor.role == "ADMIN" and actor.college_id is not None and student.college_id != actor.college_id:
        raise HTTPException(403, "This student is outside your college.")

    existing = db.scalar(
        select(PointTransaction).where(PointTransaction.reversal_of == original.transaction_id)
    )
    if existing is not None:
        return existing

    reversal = PointTransaction(
        student_id=original.student_id,
        event_id=original.event_id,
        evaluation_id=original.evaluation_id,
        points=-original.points,
        transaction_type="REVERSAL",
        reversal_of=original.transaction_id,
    )
    db.add(reversal)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(PointTransaction).where(PointTransaction.reversal_of == original.transaction_id)
        )
        if existing is None:
            raise
        return existing
    db.refresh(reversal)
    return reversal


def student_points_summary(db: Session, student_id: int) -> dict:
    transactions = db.scalars(
        select(PointTransaction)
        .where(PointTransaction.student_id == student_id)
        .order_by(PointTransaction.created_at.desc(), PointTransaction.transaction_id.desc())
    ).all()
    total_points = db.scalar(
        select(func.coalesce(func.sum(PointTransaction.points), 0)).where(
            PointTransaction.student_id == student_id
        )
    )
    events = {
        event.id: event
        for event in db.scalars(
            select(Event).where(Event.id.in_({transaction.event_id for transaction in transactions}))
        ).all()
    } if transactions else {}
    return {
        "total_points": total_points or 0,
        "transactions": [
            {
                "transaction_id": transaction.transaction_id,
                "student_id": transaction.student_id,
                "event_id": transaction.event_id,
                "event_title": events[transaction.event_id].title if transaction.event_id in events else None,
                "evaluation_id": transaction.evaluation_id,
                "points": transaction.points,
                "transaction_type": transaction.transaction_type,
                "created_at": transaction.created_at,
                "reversal_of": transaction.reversal_of,
            }
            for transaction in transactions
        ],
    }


def serialize_point_transaction(db: Session, transaction: PointTransaction) -> dict:
    event = db.get(Event, transaction.event_id)
    return {
        "transaction_id": transaction.transaction_id,
        "student_id": transaction.student_id,
        "event_id": transaction.event_id,
        "event_title": event.title if event else None,
        "evaluation_id": transaction.evaluation_id,
        "points": transaction.points,
        "transaction_type": transaction.transaction_type,
        "created_at": transaction.created_at,
        "reversal_of": transaction.reversal_of,
    }
