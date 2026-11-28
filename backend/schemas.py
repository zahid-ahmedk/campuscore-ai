from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config import settings


class LoginRequest(BaseModel):
    email: str
    password: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    code: str = Field(min_length=2, max_length=10)


class StaffCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=72)
    role: str
    department_id: int


class StudentCreate(BaseModel):
    roll_no: str
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    batch: str = Field(min_length=2, max_length=4)
    semester: int = Field(default=1, ge=1, le=8)
    department_id: int
    attendance_percentage: float = Field(default=85.0, ge=0, le=100)
    cgpa: float = Field(default=0.0, ge=0, le=4)

    @field_validator("roll_no")
    @classmethod
    def _roll(cls, v: str) -> str:
        v = v.strip().upper()
        if not settings.ROLL_NO_PATTERN.match(v):
            raise ValueError("Roll number must look like 21IT-95")
        return v


class FeeDueCreate(BaseModel):
    roll_no: Optional[str] = None
    batch: Optional[str] = None  # raise the same due for a whole batch
    semester: int = Field(ge=1, le=8)
    category: str
    custom_category: Optional[str] = None
    amount: float = Field(gt=0)


class VerifyRequest(BaseModel):
    status: str  # Verified | Rejected
    remarks: Optional[str] = Field(default=None, max_length=300)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=600)
