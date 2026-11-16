from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.database.base import Base
from app.models.category import Category
from app.models.registration import EventRegistration
from app.models.user import User
from app.services.registration_service import register_student_for_event


def create_event(client, status="PUBLISHED", capacity=1, deadline_delta=timedelta(days=2)):
    factory = client.app.state.test_session_factory
    event_table = Base.metadata.tables["events"]
    with factory() as db:
        category = db.query(Category).first()
        result = db.execute(
            event_table.insert().values(
                title=f"Test event {datetime.now(timezone.utc).timestamp()}",
                description="Test event",
                category_id=category.id,
                start_date=datetime.now(timezone.utc) + timedelta(days=4),
                end_date=datetime.now(timezone.utc) + timedelta(days=5),
                venue="Campus",
                registration_deadline=datetime.now(timezone.utc) + deadline_delta,
                capacity=capacity,
                status=status,
            )
        )
        db.commit()
        return result.inserted_primary_key[0]


def create_account(client, name, email, usn, role="STUDENT"):
    response = client.post(
        "/auth/register",
        json={
            "full_name": name,
            "email": email,
            "usn": usn,
            "department": "Engineering",
            "semester": 4,
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    if role != "STUDENT":
        factory = client.app.state.test_session_factory
        with factory() as db:
            account = db.query(User).filter_by(email=email).one()
            account.role = role
            db.commit()
    token = client.post("/auth/login", json={"email": email, "password": "SecurePass123!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_registration_duplicate_deadline_capacity_and_cancellation(client, student):
    event_id = create_event(client)
    first = client.post(f"/events/{event_id}/register", headers=student["headers"])
    duplicate = client.post(f"/events/{event_id}/register", headers=student["headers"])
    assert first.status_code == 201
    assert duplicate.status_code == 409

    second_event_id = create_event(client, capacity=0)
    assert client.post(f"/events/{second_event_id}/register", headers=student["headers"]).status_code == 409
    expired_event_id = create_event(client, deadline_delta=timedelta(days=-1))
    assert client.post(f"/events/{expired_event_id}/register", headers=student["headers"]).status_code == 409
    unpublished_id = create_event(client, status="PENDING")
    assert client.post(f"/events/{unpublished_id}/register", headers=student["headers"]).status_code == 404
    assert len(client.get("/registrations/me", headers=student["headers"]).json()) == 1


def test_only_students_can_register_and_cannot_access_anothers_records(client):
    event_id = create_event(client)
    organizer = create_account(client, "Organizer", "org@college.edu", "1XX23OR001", "ORGANIZER")
    assert client.post(f"/events/{event_id}/register", headers=organizer).status_code == 403
    no_auth = client.get("/registrations/me")
    assert no_auth.status_code == 401


def test_cancelled_registration_does_not_consume_capacity(client, student):
    event_id = create_event(client, capacity=1)
    assert client.post(f"/events/{event_id}/register", headers=student["headers"]).status_code == 201
    factory = client.app.state.test_session_factory
    with factory() as db:
        registration = db.query(EventRegistration).filter_by(event_id=event_id).one()
        registration.status = "CANCELLED"
        db.commit()

    other_student = create_account(client, "Other Student", "other@college.edu", "1XX23CS010")
    response = client.post(f"/events/{event_id}/register", headers=other_student)
    assert response.status_code == 201


def test_cancelled_registration_is_reactivated_without_duplicate_row(client, student):
    event_id = create_event(client, capacity=2)
    assert client.post(f"/events/{event_id}/register", headers=student["headers"]).status_code == 201
    factory = client.app.state.test_session_factory
    with factory() as db:
        registration = db.query(EventRegistration).filter_by(event_id=event_id).one()
        registration.status = "CANCELLED"
        db.commit()

    response = client.post(f"/events/{event_id}/register", headers=student["headers"])
    assert response.status_code == 201
    assert response.json()["status"] == "REGISTERED"
    with factory() as db:
        assert db.query(EventRegistration).filter_by(event_id=event_id).count() == 1


def test_concurrent_registrations_do_not_exceed_capacity(client, student):
    event_id = create_event(client, capacity=1)
    other_student = create_account(client, "Other Student", "other@college.edu", "1XX23CS010")
    other_user_id = client.get("/auth/me", headers=other_student).json()["id"]
    student_id = student["user"]["id"]
    factory = client.app.state.test_session_factory

    def attempt_registration(user_id):
        with factory() as db:
            user = db.get(User, user_id)
            try:
                register_student_for_event(db, user, event_id)
                return "registered"
            except HTTPException as error:
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt_registration, [student_id, other_user_id]))

    assert results.count("registered") == 1
    assert results.count(409) == 1
    with factory() as db:
        assert db.query(EventRegistration).filter_by(event_id=event_id, status="REGISTERED").count() == 1
