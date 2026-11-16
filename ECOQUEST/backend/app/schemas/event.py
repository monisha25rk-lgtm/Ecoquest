from datetime import datetime

from pydantic import BaseModel


class EventRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    organization_id: int | None = None
    organization_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    venue: str | None = None
    event_mode: str | None = None
    college_id: int | None = None
    college_name: str | None = None
    entry_fee: int | None = None
    facilities: str | None = None
    registration_deadline: datetime | None = None
    capacity: int | None = None
    available_seats: int | None = None
    eligibility_requirements: str | None = None
    participation_requirements: str | None = None
    evidence_requirements: str | None = None
    poster_path: str | None = None
    approved_eco_points: int | None = None
    proposed_eco_points: int | None = None
    review_note: str | None = None
    status: str


class EventPage(BaseModel):
    items: list[EventRead]
    page: int
    limit: int
    total: int
