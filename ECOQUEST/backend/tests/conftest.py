import os

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-with-at-least-32-characters")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db, initialize_database
from app.main import app
from app.core.config import settings


if "events" not in Base.metadata.tables:
    Table(
        "organizations",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(200), nullable=False),
    )
    Table(
        "events",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200), nullable=False),
        Column("description", Text),
        Column("organization_id", ForeignKey("organizations.id")),
        Column("category_id", ForeignKey("categories.id")),
        Column("start_date", DateTime),
        Column("end_date", DateTime),
        Column("venue", String(200)),
        Column("registration_deadline", DateTime),
        Column("capacity", Integer),
        Column("eligibility_requirements", Text),
        Column("participation_requirements", Text),
        Column("evidence_requirements", Text),
        Column("poster_path", String(500)),
        Column("approved_eco_points", Integer),
        Column("status", String(20), nullable=False),
    )


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "secret_key", "test-only-secret-key-with-at-least-32-characters")
    engine = create_engine(
        f"sqlite:///{tmp_path / 'ecoquest-test.db'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    @event.listens_for(engine, "connect")
    def enable_test_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    initialize_database(engine)
    Base.metadata.create_all(
        engine,
        tables=[Base.metadata.tables["organizations"], Base.metadata.tables["events"]],
    )
    initialize_database(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    app.state.test_session_factory = session_factory

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def student(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Asha Student",
            "email": "asha@college.edu",
            "usn": "1XX23CS001",
            "department": "Computer Science",
            "semester": 5,
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    login = client.post("/auth/login", json={"email": "asha@college.edu", "password": "SecurePass123!"})
    assert login.status_code == 200
    return {"user": response.json(), "headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}
