import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.base import Base

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False, "timeout": 30} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database(bind: Engine = engine) -> None:
    from app.models import category, college, event, faculty_assignment, notification, organization, point_transaction, progress, registration, review, submission, teacher_profile, user  # noqa: F401

    Base.metadata.create_all(bind=bind, tables=[
        college.College.__table__, user.User.__table__, category.Category.__table__, organization.Organization.__table__, event.Event.__table__,
        registration.EventRegistration.__table__, progress.ProgressLog.__table__, submission.Submission.__table__,
        submission.SubmissionFile.__table__, review.Review.__table__, notification.Notification.__table__,
        faculty_assignment.FacultyAssignment.__table__, teacher_profile.TeacherProfile.__table__,
        point_transaction.PointTransaction.__table__,
    ])
    _add_shared_columns(bind)
    category.seed_categories(SessionLocal if bind is engine else sessionmaker(bind=bind))


def _add_shared_columns(bind: Engine) -> None:
    """Add Person 2 columns to an existing Person 1/shared SQLite database."""
    if bind.dialect.name != "sqlite":
        return
    additions = {
        "users": {"college_id": "INTEGER REFERENCES colleges(id)"},
        "colleges": {
            "official_email": "TEXT", "contact_number": "TEXT", "address": "TEXT",
            "city": "TEXT", "state": "TEXT", "admin_user_id": "INTEGER REFERENCES users(id)",
        },
        "organizations": {
            "college_id": "INTEGER REFERENCES colleges(id)",
            "organization_type": "TEXT NOT NULL DEFAULT 'Other'",
            "department_affiliation": "TEXT",
            "supporting_document_original_name": "TEXT",
            "supporting_document_path": "TEXT",
            "supporting_document_content_type": "TEXT",
            "supporting_document_size_bytes": "INTEGER",
        },
        "events": {
            "college_id": "INTEGER REFERENCES colleges(id)", "event_mode": "TEXT NOT NULL DEFAULT 'IN_PERSON'",
            "approved_by_id": "INTEGER REFERENCES users(id)", "entry_fee": "INTEGER NOT NULL DEFAULT 0", "facilities": "TEXT",
        },
        "submissions": {"assigned_teacher_id": "INTEGER REFERENCES users(id)", "version": "INTEGER NOT NULL DEFAULT 1"},
        "reviews": {"grade": "INTEGER", "submission_version": "INTEGER NOT NULL DEFAULT 1"},
    }
    inspector = inspect(bind)
    with bind.begin() as connection:
        for table_name, columns in additions.items():
            if table_name not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}'))
