from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.services.points_service import (
    reverse_point_transaction,
    serialize_point_transaction,
    student_points_summary,
)

router = APIRouter(prefix="/points", tags=["Eco Points"])


@router.get("/me")
def my_points(db: Session = Depends(get_db), student: User = Depends(require_role("STUDENT"))):
    return student_points_summary(db, student.id)


@router.post("/transactions/{transaction_id}/reverse")
def reverse_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("TEACHER", "ADMIN")),
):
    transaction = reverse_point_transaction(db, transaction_id, actor)
    return serialize_point_transaction(db, transaction)
