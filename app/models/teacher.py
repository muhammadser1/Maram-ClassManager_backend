from app.models.base_user import User, Role
from datetime import datetime, date
from typing import Optional


class Teacher(User):
    """ Teacher model with classroom management and email verification """

    def __init__(self, username: str, email: str, password: str,
                 birthday: Optional[date] = None,  # ✅ Added birthday
                 verified: bool = False, verification_token: Optional[str] = None,
                 verification_expiry: Optional[datetime] = None):
        super().__init__(
            username, email, password, Role.TEACHER,
            birthday=birthday,
            verified=verified, verification_token=verification_token,
            verification_expiry=verification_expiry
        )

    def create_assignment(self, assignment_data: dict, assignments_collection):
        """ Creates an assignment for students """
        assignments_collection.insert_one(assignment_data)
        return {"message": "Assignment created successfully"}

    def submit_lesson(self, lesson_data: dict, lessons_collection):
        """ Submits a new lesson """
        lessons_collection.insert_one(lesson_data)
        return {"message": "Lesson submitted successfully"}

    def view_statistics(self, lessons_collection):
        """ Retrieves statistics for the teacher's lessons """
        return list(lessons_collection.find({"teacher": self.username}, {"_id": 0}))

    def forgot_password(self, email: str):
        """ Triggers password reset process """
        return {"message": f"Password reset link sent to {email}"}

    def add_suggestion(self, suggestion: str, suggestions_collection):
        """ Adds a suggestion """
        suggestions_collection.insert_one({"suggestion": suggestion})
        return {"message": "Suggestion added successfully"}
