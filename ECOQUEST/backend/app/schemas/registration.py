from datetime import datetime

from pydantic import BaseModel

from app.schemas.event import EventRead


class RegistrationRead(BaseModel):
    id: int
    student_id: int
    event_id: int
    registration_date: datetime
    status: str
    event: EventRead
