from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class IndividualLessonBase(BaseModel):
    date: datetime
    teacher_name: str
    student_name: str
    hours: float
    subject: str
    education_level: str
    approved: bool = Field(default=False, description="Approval status by admin")


class GroupLessonBase(BaseModel):
    date: datetime
    teacher_name: str
    student_names: List[str]
    hours: float
    subject: str
    education_level: str
    approved: bool = Field(default=False, description="Approval status by admin")