from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ORGANIZATION_TYPES = (
    "College Club", "Department", "NGO", "Student Association", "External Organization", "Other"
)


class OrganizationRegistration(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    organization_type: str = Field(pattern="^(College Club|Department|NGO|Student Association|External Organization|Other)$")
    description: str = Field(min_length=10, max_length=4000)
    official_email: EmailStr
    contact_number: str = Field(min_length=5, max_length=30)
    department_affiliation: str | None = Field(default=None, max_length=160)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    name: str
    organization_type: str
    description: str | None
    contact_email: str | None
    contact_phone: str | None
    department_affiliation: str | None
    supporting_document_original_name: str | None
    supporting_document_content_type: str | None
    supporting_document_size_bytes: int | None
    status: str
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None


class OrganizationDecision(BaseModel):
    status: str = Field(pattern="^(APPROVED|REJECTED)$")
    review_note: str | None = Field(default=None, max_length=2000)
