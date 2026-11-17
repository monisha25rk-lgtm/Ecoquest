import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.college import College
from app.models.event import Event
from app.models.faculty_assignment import FacultyAssignment
from app.models.point_transaction import PointTransaction
from app.models.registration import EventRegistration
from app.models.review import Review
from app.models.submission import Submission
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password
from app.services.points_service import allocate_points_for_evaluation


def _review_context(client, student_id):
    session_factory = client.app.state.test_session_factory
    with session_factory() as db:
        college = College(name=f"Test College {student_id}", code=f"TC{student_id}")
        db.add(college)
        db.flush()
        student = db.get(User, student_id)
        student.college_id = college.id
        teacher = User(
            full_name=f"Teacher {student_id}",
            email=f"teacher{student_id}@college.edu",
            usn=f"FAC-{student_id}",
            department="Environmental Science",
            semester=0,
            password_hash=hash_password("SecurePass123!"),
            role="TEACHER",
            college_id=college.id,
        )
        event = Event(
            title=f"Eco Event {student_id}",
            category_id=1,
            proposed_eco_points=100,
            approved_eco_points=100,
            status="PUBLISHED",
            college_id=college.id,
        )
        db.add_all([teacher, event])
        db.flush()
        registration = EventRegistration(
            student_id=student.id,
            event_id=event.id,
            status="REGISTERED",
        )
        db.add(registration)
        db.flush()
        submission = Submission(
            registration_id=registration.id,
            status="PENDING",
            assigned_teacher_id=teacher.id,
            version=1,
        )
        assignment = FacultyAssignment(
            college_id=college.id,
            teacher_id=teacher.id,
            student_id=student.id,
            student_usn=student.usn,
            status="ACTIVE",
        )
        db.add_all([submission, assignment])
        db.commit()
        token, _ = create_access_token(teacher)
        return {
            "event_id": event.id,
            "registration_id": registration.id,
            "submission_id": submission.id,
            "teacher_id": teacher.id,
            "teacher_headers": {"Authorization": f"Bearer {token}"},
        }


def _approve(client, context, *, grade=80):
    return client.patch(
        f"/teacher/submissions/{context['submission_id']}/review",
        headers=context["teacher_headers"],
        json={"decision": "APPROVED", "grade": grade},
    )


def _other_teacher_headers(client, student_id):
    with client.app.state.test_session_factory() as db:
        student = db.get(User, student_id)
        teacher = User(
            full_name="Other Teacher",
            email="other.teacher@college.edu",
            usn="FAC-OTHER",
            department="Environmental Science",
            semester=0,
            password_hash=hash_password("SecurePass123!"),
            role="TEACHER",
            college_id=student.college_id,
        )
        db.add(teacher)
        db.commit()
        token, _ = create_access_token(teacher)
        return {"Authorization": f"Bearer {token}"}


def _college_admin_headers(client, student_id):
    with client.app.state.test_session_factory() as db:
        student = db.get(User, student_id)
        admin = User(
            full_name="College Admin",
            email="college.admin@college.edu",
            usn="ADM-TEST",
            department="Administration",
            semester=0,
            password_hash=hash_password("SecurePass123!"),
            role="ADMIN",
            college_id=student.college_id,
        )
        db.add(admin)
        db.commit()
        token, _ = create_access_token(admin)
        return {"Authorization": f"Bearer {token}"}


def test_approved_evaluation_awards_once_and_points_are_student_scoped(client, student):
    first = _review_context(client, student["user"]["id"])
    assert _approve(client, first).status_code == 200
    assert _approve(client, first).status_code == 200

    second_student_response = client.post(
        "/auth/register",
        json={
            "full_name": "Second Student",
            "email": "second@college.edu",
            "usn": "1XX23CS020",
            "department": "Environmental Science",
            "semester": 3,
            "password": "SecurePass123!",
        },
    )
    assert second_student_response.status_code == 201
    second_student_id = second_student_response.json()["id"]
    second = _review_context(client, second_student_id)
    assert _approve(client, second).status_code == 200

    first_points = client.get("/points/me", headers=student["headers"])
    second_login = client.post(
        "/auth/login",
        json={"email": "second@college.edu", "password": "SecurePass123!"},
    )
    second_points = client.get(
        "/points/me",
        headers={"Authorization": f"Bearer {second_login.json()['access_token']}"},
    )
    assert first_points.status_code == second_points.status_code == 200
    assert first_points.json()["total_points"] == 80
    assert second_points.json()["total_points"] == 80
    assert len(first_points.json()["transactions"]) == 1
    assert len(second_points.json()["transactions"]) == 1
    assert first_points.json()["transactions"][0]["event_id"] == first["event_id"]
    assert second_points.json()["transactions"][0]["event_id"] == second["event_id"]

    with client.app.state.test_session_factory() as db:
        assert db.scalar(select(func.count(PointTransaction.transaction_id))) == 2
        assert db.scalar(select(func.count(Review.id)).where(Review.submission_id == first["submission_id"])) == 1


def test_pending_and_rejected_evaluations_do_not_award_points(client, student):
    context = _review_context(client, student["user"]["id"])
    with client.app.state.test_session_factory() as db:
        review = Review(
            submission_id=context["submission_id"],
            reviewer_id=context["teacher_id"],
            decision="PENDING",
            grade=100,
            submission_version=1,
        )
        db.add(review)
        db.flush()
        with pytest.raises(HTTPException) as error:
            allocate_points_for_evaluation(
                db=db,
                registration_id=context["registration_id"],
                evaluation_id=review.id,
            )
        assert error.value.status_code == 409
        db.rollback()

    response = client.patch(
        f"/teacher/submissions/{context['submission_id']}/review",
        headers=context["teacher_headers"],
        json={"decision": "REJECTED", "note": "Evidence does not meet requirements."},
    )
    assert response.status_code == 200
    points = client.get("/points/me", headers=student["headers"])
    assert points.json()["total_points"] == 0
    assert points.json()["transactions"] == []


def test_reversal_is_separate_idempotent_and_reduces_total(client, student):
    context = _review_context(client, student["user"]["id"])
    assert _approve(client, context, grade=100).status_code == 200
    award = client.get("/points/me", headers=student["headers"]).json()["transactions"][0]

    reversal_response = client.post(
        f"/points/transactions/{award['transaction_id']}/reverse",
        headers=context["teacher_headers"],
    )
    repeated_response = client.post(
        f"/points/transactions/{award['transaction_id']}/reverse",
        headers=context["teacher_headers"],
    )
    assert reversal_response.status_code == repeated_response.status_code == 200
    assert reversal_response.json()["transaction_type"] == "REVERSAL"
    assert reversal_response.json()["points"] == -100
    assert repeated_response.json()["transaction_id"] == reversal_response.json()["transaction_id"]

    points = client.get("/points/me", headers=student["headers"]).json()
    assert points["total_points"] == 0
    assert len(points["transactions"]) == 2


def test_registration_evidence_review_awards_points_end_to_end(client, student, monkeypatch, tmp_path):
    context = _review_context(client, student["user"]["id"])
    with client.app.state.test_session_factory() as db:
        submission = db.get(Submission, context["submission_id"])
        registration = db.get(EventRegistration, context["registration_id"])
        db.delete(submission)
        db.delete(registration)
        db.commit()

    from app.services import person2_service

    monkeypatch.setattr(person2_service, "UPLOAD_ROOT", tmp_path)
    registration_response = client.post(
        f"/events/{context['event_id']}/register",
        headers=student["headers"],
    )
    assert registration_response.status_code == 201
    registration_id = registration_response.json()["id"]
    evidence_response = client.post(
        f"/registrations/{registration_id}/submission",
        headers=student["headers"],
        data={"participation_dates": "2026-11-17"},
        files=[("files", ("participation.pdf", b"evidence", "application/pdf"))],
    )
    assert evidence_response.status_code == 200
    assert evidence_response.json()["status"] == "PENDING"
    assert len(evidence_response.json()["files"]) == 1

    context["submission_id"] = evidence_response.json()["id"]
    context["registration_id"] = registration_id
    assert _approve(client, context, grade=75).status_code == 200
    points = client.get("/points/me", headers=student["headers"]).json()
    assert points["total_points"] == 75
    assert points["transactions"][0]["event_id"] == context["event_id"]


def test_only_evaluating_faculty_or_college_admin_can_reverse(client, student):
    context = _review_context(client, student["user"]["id"])
    assert _approve(client, context).status_code == 200
    award = client.get("/points/me", headers=student["headers"]).json()["transactions"][0]

    forbidden = client.post(
        f"/points/transactions/{award['transaction_id']}/reverse",
        headers=_other_teacher_headers(client, student["user"]["id"]),
    )
    assert forbidden.status_code == 403
    authorized = client.post(
        f"/points/transactions/{award['transaction_id']}/reverse",
        headers=_college_admin_headers(client, student["user"]["id"]),
    )
    assert authorized.status_code == 200
