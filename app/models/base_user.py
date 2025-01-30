from datetime import date, datetime
from typing import Optional
from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class User:
    """
    Base User Model with common attributes, including email verification.
    """

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        role: Role,
        birthday: Optional[date] = None,
        verified: bool = False,
        verification_token: Optional[str] = None,
        verification_expiry: Optional[datetime] = None
    ):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.birthday = birthday
        self.verified = verified
        self.verification_token = verification_token
        self.verification_expiry = verification_expiry

    def save(self, users_collection):
        """ Save user data to MongoDB """
        user_data = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "role": self.role.value,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "verified": self.verified,
            "verification_token": self.verification_token,
            "verification_expiry": self.verification_expiry
        }
        users_collection.insert_one(user_data)
        return {"message": "User saved successfully"}
