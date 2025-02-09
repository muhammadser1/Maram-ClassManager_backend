from app.models.base_user import User, Role
from datetime import datetime, date
from typing import Optional
from bson import ObjectId


class Teacher(User):
    """ Teacher model with lesson management and email verification """

    def __init__(self, username: str, email: str, password: str,
                 birthday: Optional[date] = None,
                 verified: bool = False, verification_token: Optional[str] = None,
                 verification_expiry: Optional[datetime] = None):
        super().__init__(
            username, email, password, Role.TEACHER,
            birthday=birthday,
            verified=verified, verification_token=verification_token,
            verification_expiry=verification_expiry
        )

    def submit_lesson(self, lesson_data: dict, lessons_collection):
        """ Submits a new lesson with pending approval (Supports Individual & Group Lessons) """
        lesson_data["approved"] = False
        lesson_data["teacher_name"] = self.username

        if "student_names" in lesson_data:
            lesson_data["lesson_type"] = "group"
        else:
            lesson_data["lesson_type"] = "individual"

        result = lessons_collection.insert_one(lesson_data)
        return {"message": "Lesson submitted successfully, pending approval", "lessonId": str(result.inserted_id)}

    def edit_lesson(self, lesson_id: str, lesson_updates: dict, lessons_collection):
        """ Allows a teacher to edit their own lesson before approval """
        try:
            lesson_object_id = ObjectId(lesson_id)
            lesson = lessons_collection.find_one(
                {"_id": lesson_object_id, "teacher_name": self.username, "approved": False})

            if not lesson:
                return {"error": "Lesson not found or unauthorized to edit"}

            if "approved" in lesson_updates:
                del lesson_updates["approved"]

            lessons_collection.update_one({"_id": lesson_object_id}, {"$set": lesson_updates})
            return {"message": "Lesson updated successfully", "lessonId": lesson_id}
        except Exception as e:
            return {"error": f"Error updating lesson: {str(e)}"}

    def delete_lesson(self, lesson_id: str, lessons_collection):
        """ Allows a teacher to delete their own lesson before approval """
        try:
            lesson_object_id = ObjectId(lesson_id)
            result = lessons_collection.delete_one(
                {"_id": lesson_object_id, "teacher_name": self.username, "approved": False})

            if result.deleted_count == 0:
                return {"error": "Lesson not found or unauthorized to delete"}

            return {"message": "Lesson deleted successfully", "lessonId": lesson_id}
        except Exception as e:
            return {"error": f"Error deleting lesson: {str(e)}"}

    def view_statistics(self, lessons_collection):
        """ Retrieves total hours taught, grouped by education level """
        lessons = list(lessons_collection.find({"teacher_name": self.username, "approved": True}))

        total_hours = sum(lesson.get("hours", 0) for lesson in lessons)
        grouped_by_level = {}

        for lesson in lessons:
            level = lesson.get("education_level", "Unknown Level")
            grouped_by_level.setdefault(level, 0)
            grouped_by_level[level] += lesson.get("hours", 0)

        return {
            "message": "Teacher statistics retrieved successfully",
            "total_hours": total_hours,
            "lessons_by_level": grouped_by_level
        }
