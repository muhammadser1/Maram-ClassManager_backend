from app.models.base_user import User, Role
from datetime import datetime, date
from typing import Optional
from bson import ObjectId


class Admin(User):

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
        try:
            lesson_object_id = ObjectId(lesson_id)
            result = lessons_collection.update_one({"_id": lesson_object_id}, {"$set": {"approved": True}})

            if result.matched_count == 0:
                return {"error": "Lesson not found"}

            return {"message": "Lesson approved successfully", "lessonId": lesson_id}
        except Exception as e:
            return {"error": f"Error approving lesson: {str(e)}"}

    def reject_lesson(self, lesson_id: str, lessons_collection):
        """ Rejects a lesson submitted by a teacher """
        try:
            lesson_object_id = ObjectId(lesson_id)
            result = lessons_collection.update_one({"_id": lesson_object_id}, {"$set": {"approved": False}})

            if result.matched_count == 0:
                return {"error": "Lesson not found"}

            return {"message": "Lesson rejected", "lessonId": lesson_id}
        except Exception as e:
            return {"error": f"Error rejecting lesson: {str(e)}"}

    def view_all_lessons_statistics(self, lessons_collection, approved: Optional[bool] = None):
        """ Retrieves statistics of all lessons with an optional filter """
        query = {} if approved is None else {"approved": approved}
        lessons = list(lessons_collection.find(query, {"_id": 0}))
        return {
            "message": "Lesson statistics retrieved successfully",
            "total_lessons": len(lessons),
            "lessons": lessons
        }
