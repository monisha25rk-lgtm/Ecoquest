from datetime import datetime, timedelta, timezone

from jose import jwt
from pwdlib import PasswordHash
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.models.teacher_profile import TeacherProfile
from app.models.college import College

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def create_access_token(user: User) -> tuple[str, int]:
    expires_in = settings.access_token_expire_minutes * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token = jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": expires_at},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token, expires_in


def register_student(db: Session, *, full_name: str, email: str, usn: str, department: str, semester: int, password: str) -> User:
    normalized_email = email.strip().lower()
    normalized_usn = usn.strip().upper()
    exists = db.scalar(
        select(User.id).where(or_(User.email == normalized_email, User.usn == normalized_usn)).limit(1)
    )
    if exists is not None:
        raise ValueError("An account with this email or USN already exists.")
    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        usn=normalized_usn,
        department=department.strip(),
        semester=semester,
        password_hash=hash_password(password),
        role="STUDENT",
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return user


def register_role_account(db: Session, payload) -> User:
    normalized_email = payload.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == normalized_email)):
        raise ValueError("An account with this email already exists.")
    if payload.role == "ORGANIZER":
        required = [payload.organization_name, payload.organization_type, payload.organization_description, payload.organization_official_email, payload.contact_number]
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("Complete organization details are required.")
        code = "ORG"
    elif payload.role == "TEACHER":
        required = [payload.employee_id, payload.department, payload.designation]
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("Employee ID, department and designation are required.")
        code = "FAC"
    else:
        required = [payload.college_name, payload.college_code, payload.college_official_email, payload.contact_number, payload.college_city, payload.college_state]
        if any(not value or not str(value).strip() for value in required):
            raise ValueError("Complete college details are required.")
        if db.scalar(select(College.id).where((College.code == payload.college_code.strip()) | (College.name == payload.college_name.strip()))):
            raise ValueError("A college with this name or code already exists.")
        code = "ADM"
    stored_role = "ADMIN" if payload.role == "COLLEGE_ADMIN" else payload.role
    user = User(full_name=payload.full_name.strip(), email=normalized_email, usn=f"{code}-{normalized_email}", department=(payload.department or "Organization").strip(), semester=0, password_hash=hash_password(payload.password), role=stored_role)
    db.add(user)
    db.flush()
    if payload.role == "ORGANIZER":
        db.add(Organization(owner_id=user.id, name=payload.organization_name.strip(), organization_type=payload.organization_type, description=payload.organization_description.strip(), contact_email=str(payload.organization_official_email), contact_phone=payload.contact_number.strip(), department_affiliation=payload.affiliation, status="PENDING"))
    elif payload.role == "TEACHER":
        db.add(TeacherProfile(user_id=user.id, employee_id=payload.employee_id.strip(), department=payload.department.strip(), designation=payload.designation.strip(), official_email=normalized_email, contact_number=payload.contact_number, status="ACTIVE"))
    else:
        college = College(name=payload.college_name.strip(), code=payload.college_code.strip(), official_email=str(payload.college_official_email), contact_number=payload.contact_number.strip(), address=payload.college_address, city=payload.college_city.strip(), state=payload.college_state.strip(), admin_user_id=user.id)
        db.add(college)
        db.flush()
        user.college_id = college.id
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    return user
