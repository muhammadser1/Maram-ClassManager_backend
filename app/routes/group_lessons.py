from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict
from app.core.dependencies import get_group_lessons_collection, get_current_authenticated_user, \
    get_individual_lessons_collection
from app.routes.teacher import fetch_lessons
from app.schemas.Lesson import GroupLessonBase
from datetime import datetime

router = APIRouter()

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_group_lessons_collection, role_required, get_current_authenticated_user
from app.schemas.Lesson import GroupLessonBase

router = APIRouter()


@router.post("/submit", response_model=dict)
def submit_group_lesson(
        lesson: GroupLessonBase,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Submit a new group lesson (Pending Approval)."""
    lesson_data = lesson.dict()
    lesson_data["teacher_name"] = current_user["username"]
    lesson_data["approved"] = False

    inserted = lessons_collection.insert_one(lesson_data)
    return {"message": "Group lesson submitted successfully, pending approval", "lesson_id": str(inserted.inserted_id)}


@router.get("/pending-lessons", response_model=dict)
def get_pending_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve all pending group lessons for the authenticated teacher."""
    return {"message": "Pending group lessons retrieved successfully",
            "pending_lessons": fetch_lessons(lessons_collection, current_user, False)}


@router.get("/approved-lessons", response_model=dict)
def get_approved_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve all approved group lessons for the authenticated teacher."""
    return {"message": "Approved group lessons retrieved successfully",
            "approved_lessons": fetch_lessons(lessons_collection, current_user, True)}


@router.delete("/delete-lesson/{lesson_id}", response_model=dict)
def delete_group_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Delete a group lesson (Only for the lesson owner)."""
    result = lessons_collection.delete_one(
        {"_id": ObjectId(lesson_id), "teacher_name": current_user["username"], "approved": False})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to delete")

    return {"message": "Group lesson deleted successfully"}


@router.put("/update-lesson/{lesson_id}", response_model=dict)
def update_group_lesson(
        lesson_id: str,
        lesson_updates: Dict,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Update a group lesson's details (Only for the lesson owner)."""
    print(f"🛠 Updating Group Lesson ID: {lesson_id} for User: {current_user['username']}")

    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"]})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to update")

    lesson_updates.pop("_id", None)

    lessons_collection.update_one({"_id": ObjectId(lesson_id)}, {"$set": lesson_updates})

    return {"message": "Group lesson updated successfully"}


@router.get("/dashboard-overview", response_model=Dict)
def get_dashboard_overview(
        month: int = Query(None, description="Filter lessons by month (1-12)"),
        individual_lessons_collection=Depends(get_individual_lessons_collection),
        group_lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("teacher"))
):
    """Retrieve dashboard statistics for the authenticated teacher filtered by month."""
    print(f"👤 Fetching dashboard overview for: {current_user['username']} | Month: {month}")

    # ✅ Fetch only necessary fields
    projection = {"hours": 1, "education_level": 1, "date": 1}
    individual_lessons = list(
        individual_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}, projection)
    )
    group_lessons = list(
        group_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}, projection)
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
        return None  # If no date field

    # ✅ Filter by month if provided
    if month:
        individual_lessons = [lesson for lesson in individual_lessons if get_month(lesson) == month]
        group_lessons = [lesson for lesson in group_lessons if get_month(lesson) == month]

    # ✅ Calculate statistics
    total_lessons = len(individual_lessons) + len(group_lessons)
    total_hours = sum(lesson.get("hours", 0) for lesson in individual_lessons) + sum(
        lesson.get("hours", 0) for lesson in group_lessons)

    # ✅ Define education levels
    education_levels = ["ابتدائي", "إعدادي", "ثانوي"]

    # ✅ Calculate hours by education level
    def calculate_hours_by_level(lessons):
        return {
            level: sum(lesson["hours"] for lesson in lessons if lesson.get("education_level") == level)
            for level in education_levels
        }

    return {
        "message": "Dashboard overview data retrieved successfully",
        "total_lessons": total_lessons,
        "total_hours": total_hours,
        "individual_hours_by_level": calculate_hours_by_level(individual_lessons),
        "group_hours_by_level": calculate_hours_by_level(group_lessons)
    }
