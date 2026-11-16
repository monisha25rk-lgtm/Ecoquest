from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=10000)
    category_id: int = Field(ge=1)
    start_date: datetime
    end_date: datetime
    venue: str = Field(min_length=2, max_length=240)
    event_mode: str = Field(default="IN_PERSON", pattern="^(IN_PERSON|ONLINE|HYBRID)$")
    entry_fee: int = Field(default=0, ge=0, le=100000)
    facilities: str | None = Field(default=None, max_length=4000)
    registration_deadline: datetime
    capacity: int = Field(ge=1, le=100000)
    eligibility_requirements: str = Field(min_length=2, max_length=4000)
    participation_requirements: str = Field(min_length=2, max_length=4000)
    evidence_requirements: str = Field(min_length=2, max_length=4000)
    proposed_eco_points: int = Field(ge=0, le=10000)


class EventDecision(BaseModel):
    status: str = Field(pattern="^(PUBLISHED|REJECTED)$")
    approved_eco_points: int | None = Field(default=None, ge=0, le=10000)
    review_note: str | None = Field(default=None, max_length=2000)


class ProgressCreate(BaseModel):
    participation_date: date
    progress_note: str = Field(min_length=2, max_length=4000)


class ProgressRead(ProgressCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    registration_id: int
    created_at: datetime


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    registration_id: int
    status: str
    participation_dates: str | None
    student_note: str | None
    submitted_at: datetime | None
    files: list[dict]
    reviews: list[dict]


class ReviewCreate(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED|CHANGES_REQUESTED)$")
    grade: int | None = Field(default=None, ge=0, le=100)
    note: str | None = Field(default=None, max_length=4000)


class FacultyAssignmentCreate(BaseModel):
    teacher_id: int = Field(ge=1)
    student_usn: str = Field(min_length=3, max_length=32)


class FacultyAssignmentRangeCreate(BaseModel):
    teacher_id: int = Field(ge=1)
    start_usn: str = Field(min_length=3, max_length=32)
    end_usn: str = Field(min_length=3, max_length=32)


class FacultyAssignmentRead(BaseModel):
    id: int
    college_id: int
    teacher_id: int
    teacher_name: str
    student_id: int
    student_name: str
    student_usn: str
    student_department: str | None = None
    status: str
    assigned_at: datetime
    updated_at: datetime


class FacultyAssignmentRangeRead(BaseModel):
    assignments: list[FacultyAssignmentRead]
    missing_usns: list[str]
    assigned_count: int


class CollegeRead(BaseModel):
    id: int
    name: str
    code: str | None = None


class CollegeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str | None = Field(default=None, max_length=40)


class UserRoleUpdate(BaseModel):
    role: str = Field(pattern="^(TEACHER|STUDENT)$")
