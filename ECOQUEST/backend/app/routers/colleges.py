from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.college import College
from app.models.user import User
from app.schemas.person2 import CollegeCreate, CollegeRead, UserRoleUpdate

router = APIRouter(tags=["Colleges"])


@router.get("/colleges", response_model=list[CollegeRead])
def list_colleges(db: Session = Depends(get_db)):
    return db.scalars(select(College).order_by(College.name)).all()


@router.post("/admin/colleges", response_model=CollegeRead, status_code=201)
def create_college(payload: CollegeCreate, db: Session = Depends(get_db), _: User = Depends(require_role("ADMIN"))):
    if db.scalar(select(College).where(College.name == payload.name.strip())):
        raise HTTPException(409, "A college with this name already exists.")
    college = College(name=payload.name.strip(), code=payload.code.strip() if payload.code else None)
    db.add(college); db.commit(); db.refresh(college)
    return college


@router.patch("/admin/users/{user_id}/role")
def update_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found.")
    if admin.college_id is not None and user.college_id not in (None, admin.college_id):
        raise HTTPException(403, "This user is outside your authorized college.")
    user.role = payload.role
    db.commit()
    return {"id": user.id, "role": user.role}
