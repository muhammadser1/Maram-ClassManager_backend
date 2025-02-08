from pydantic import BaseModel, EmailStr, Field, SecretStr
from typing import Optional
from datetime import datetime, date
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class ResendVerificationRequest(BaseModel):
    email: str


class UserLogin(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserBase(BaseModel):
    """ Base schema for users """
    username: str = Field(..., min_length=1, max_length=50, title="Username")
    email: EmailStr = Field(..., title="Email Address")
    role: Role = Field(default="teacher", title="User Role")
    birthday: Optional[date] = Field(None, title="User Birthday")
    password: SecretStr = Field(..., min_length=1, title="Password", description="User's password (min 8 chars)")

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }
