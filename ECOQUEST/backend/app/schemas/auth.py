from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class TokenUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: str


class StudentRegistration(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    usn: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9/-]+$")
    department: str = Field(min_length=2, max_length=120)
    semester: int = Field(ge=1, le=12)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name", "department")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be blank.")
        return normalized


class RoleRegistration(BaseModel):
    role: str = Field(pattern="^(ORGANIZER|TEACHER|COLLEGE_ADMIN)$")
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str | None = Field(default=None, max_length=200)
    organization_type: str | None = Field(default=None, max_length=40)
    organization_description: str | None = Field(default=None, min_length=10, max_length=4000)
    organization_official_email: EmailStr | None = None
    contact_number: str | None = Field(default=None, max_length=30)
    affiliation: str | None = Field(default=None, max_length=160)
    employee_id: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=120)
    designation: str | None = Field(default=None, max_length=100)
    college_name: str | None = Field(default=None, max_length=200)
    college_code: str | None = Field(default=None, max_length=30)
    college_official_email: EmailStr | None = None
    college_address: str | None = Field(default=None, max_length=4000)
    college_city: str | None = Field(default=None, max_length=100)
    college_state: str | None = Field(default=None, max_length=100)

    @field_validator("organization_official_email", "college_official_email", mode="before")
    @classmethod
    def blank_email_is_none(cls, value):
        return None if value == "" else value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: TokenUser
