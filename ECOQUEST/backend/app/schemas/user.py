from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    usn: str
    department: str
    semester: int
    college_id: int | None = None
    role: str
    is_active: bool
    created_at: datetime
