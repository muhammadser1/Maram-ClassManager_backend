from app.models.base_user import User, Role
from datetime import datetime, date
from typing import Optional

class Admin(User):
    """ Admin model with extra permissions and email verification """

    def __init__(self, username: str, email: str, password: str,
                 birthday: Optional[date] = None,
                 verified: bool = False, verification_token: Optional[str] = None,
                 verification_expiry: Optional[datetime] = None):
        super().__init__(
            username, email, password, Role.ADMIN,
            birthday=birthday,
            verified=verified, verification_token=verification_token,
            verification_expiry=verification_expiry
        )

    def approve_lesson(self, lesson_id: str, lessons_collection):
        """ Approves a lesson submitted by a teacher """
        lessons_collection.update_one({"_id": lesson_id}, {"$set": {"status": "approved"}})
        return {"message": "Lesson approved successfully"}

    def reject_lesson(self, lesson_id: str, lessons_collection):
        """ Rejects a lesson submitted by a teacher """
        lessons_collection.update_one({"_id": lesson_id}, {"$set": {"status": "rejected"}})
        return {"message": "Lesson rejected"}

    def view_all_lessons_statistics(self, lessons_collection):
        """ Retrieves statistics of all lessons """
        return list(lessons_collection.find({}, {"_id": 0}))

    def add_suggestion(self, suggestion: str, suggestions_collection):
        """ Adds a suggestion """
        suggestions_collection.insert_one({"suggestion": suggestion})
        return {"message": "Suggestion added successfully"}
