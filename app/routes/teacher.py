from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_individual_lessons_collection, role_required, get_current_authenticated_user, get_users_collection
from app.schemas.Lesson import IndividualLessonBase
from datetime import datetime

router = APIRouter()


@router.post("/submit", response_model=dict)
def submit_lesson(
        lesson: IndividualLessonBase,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Submit a new lesson (Pending Approval)."""
    lesson_data = lesson.dict()
    lesson_data["teacher_name"] = current_user["username"]
    lesson_data["approved"] = False

    inserted = lessons_collection.insert_one(lesson_data)

    return {"message": "Lesson submitted successfully, pending approval", "lesson_id": str(inserted.inserted_id)}


def fetch_lessons(lessons_collection, current_user, approved_status):
    """Helper function to fetch lessons based on approval status."""
    return [
        {**lesson, "_id": str(lesson["_id"])}
        for lesson in lessons_collection.find({"teacher_name": current_user["username"], "approved": approved_status})
    ]


@router.get("/pending-lessons", response_model=dict)
def get_pending_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve all pending lessons for the authenticated teacher."""
    return {"message": "Pending lessons retrieved successfully", "pending_lessons": fetch_lessons(lessons_collection, current_user, False)}


@router.get("/approved-lessons", response_model=dict)
def get_approved_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve all approved lessons for the authenticated teacher."""
    return {"message": "Approved lessons retrieved successfully", "approved_lessons": fetch_lessons(lessons_collection, current_user, True)}


@router.delete("/delete-lesson/{lesson_id}", response_model=dict)
def delete_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Delete a lesson (Only for the lesson owner)."""
    result = lessons_collection.delete_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"], "approved": False})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to delete")

    return {"message": "Lesson deleted successfully"}


@router.put("/update-lesson/{lesson_id}", response_model=dict)
def update_lesson(
        lesson_id: str,
        lesson_updates: dict,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Update a lesson's details (Only for the lesson owner)."""
    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"], "approved": False})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to update")

    if "_id" in lesson_updates:
        del lesson_updates["_id"]

    lessons_collection.update_one({"_id": ObjectId(lesson_id)}, {"$set": lesson_updates})

    return {"message": "Lesson updated successfully"}



@router.get("/teacher-individual-stats", response_model=dict)
def get_teacher_individual_stats(
        month: int = Query(None, description="Filter lessons by month (1-12)"),
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve statistics for the authenticated teacher's individual lessons."""
    print(f"📊 Fetching individual lesson stats for: {current_user['username']} | Month: {month}")

    # ✅ Fetch necessary fields
    projection = {"hours": 1, "education_level": 1, "date": 1}
    lessons = list(
        lessons_collection.find({"teacher_name": current_user["username"], "approved": True}, projection)
    )

    # ✅ Extract month safely
    def get_month(lesson):
        date_value = lesson.get("date")
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value).month
            except ValueError:
                return None
        elif isinstance(date_value, datetime):
            return date_value.month
        return None

    # ✅ Filter by month if provided
    if month:
        lessons = [lesson for lesson in lessons if get_month(lesson) == month]

    # ✅ Calculate statistics
    total_lessons = len(lessons)
    total_hours = sum(lesson.get("hours", 0) for lesson in lessons)

    # ✅ Define education levels
    education_levels = ["ابتدائي", "إعدادي", "ثانوي"]

    # ✅ Calculate hours by education level
    def calculate_hours_by_level(lessons):
        return {
            level: sum(lesson["hours"] for lesson in lessons if lesson.get("education_level") == level)
            for level in education_levels
        }

    return {
        "message": "Teacher individual lesson stats retrieved successfully",
        "total_lessons": total_lessons,
        "total_hours": total_hours,
        "hours_by_education_level": calculate_hours_by_level(lessons)
    }



@router.get("/teachers-birthdays", response_model=dict)
def get_teachers_birthdays(teachers_collection=Depends(get_users_collection)):
    """Retrieve only the teachers who have a birthday today."""

    today = datetime.today().strftime("%m-%d")  # Get today's month and day (MM-DD)

    # Fetch teachers with `birthday` field
    teachers = list(teachers_collection.find({}, {"_id": 1, "username": 1, "birthday": 1}))

    today_birthdays = []
    for teacher in teachers:
        if "birthday" in teacher and teacher["birthday"]:  # Ensure field exists
            try:
                # Convert "YYYY-MM-DD" to "MM-DD" and check if it's today
                birth_month_day = datetime.strptime(teacher["birthday"], "%Y-%m-%d").strftime("%m-%d")
                if birth_month_day == today:
                    today_birthdays.append({
                        "_id": str(teacher["_id"]),
                        "name": teacher["username"],
                        "birthday": birth_month_day
                    })
            except ValueError:
                continue  # Skip invalid dates

    return {
        "message": "Today's teachers' birthdays retrieved successfully",
        "birthdays": today_birthdays
    }