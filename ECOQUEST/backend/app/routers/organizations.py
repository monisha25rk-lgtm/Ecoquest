from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationDecision, OrganizationRead, OrganizationRegistration
from app.services.person2_service import organization_for_owner, read_organization_document, register_organization, save_organization_document

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("/register", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def register(
    organization_name: str = Form(...), organization_type: str = Form(...), description: str = Form(...),
    official_email: str = Form(...), contact_number: str = Form(...), department_affiliation: str | None = Form(None),
    supporting_document: UploadFile | None = File(None), db: Session = Depends(get_db),
    user: User = Depends(require_role("ORGANIZER")),
):
    try:
        payload = OrganizationRegistration.model_validate({
            "organization_name": organization_name, "organization_type": organization_type,
            "description": description, "official_email": official_email,
            "contact_number": contact_number, "department_affiliation": department_affiliation,
        })
        document = await read_organization_document(supporting_document) if supporting_document is not None else None
        organization = register_organization(db, user, payload)
        if supporting_document is not None:
            save_organization_document(organization, document)
            db.commit(); db.refresh(organization)
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return organization

@router.get("/me", response_model=OrganizationRead)
def mine(db: Session = Depends(get_db), user: User = Depends(require_role("ORGANIZER"))): return organization_for_owner(db, user)

@router.get("", response_model=list[OrganizationRead])
def all_organizations(db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    query = select(Organization).order_by(Organization.created_at.desc())
    if admin.college_id is not None:
        # Older organizer accounts may have been created before college
        # association was added. Surface those pending requests so the
        # authorized admin can claim them for their college during approval.
        query = query.where(or_(Organization.college_id == admin.college_id, Organization.college_id.is_(None)))
    return db.scalars(query).all()

@router.patch("/{organization_id}/decision", response_model=OrganizationRead)
def decision(organization_id: int, payload: OrganizationDecision, db: Session = Depends(get_db), admin: User = Depends(require_role("ADMIN"))):
    organization = db.get(Organization, organization_id)
    if not organization: raise HTTPException(404, "Organization not found.")
    if admin.college_id is not None and organization.college_id not in (None, admin.college_id):
        raise HTTPException(403, "This organization is outside your authorized college.")
    if organization.college_id is None and admin.college_id is not None:
        organization.college_id = admin.college_id
        owner = db.get(User, organization.owner_id)
        if owner is not None and owner.college_id is None:
            owner.college_id = admin.college_id
    organization.status = payload.status
    organization.review_note = payload.review_note
    organization.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(organization)
    return organization
