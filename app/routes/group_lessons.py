from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict
from app.core.dependencies import get_group_lessons_collection, get_current_authenticated_user, \
    get_individual_lessons_collection
from app.schemas.Lesson import GroupLessonBase
from datetime import datetime

router = APIRouter()


@router.post("/submit", response_model=dict)
def submit_group_lesson(
        lesson: GroupLessonBase,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Submit a new group lesson (Pending Approval)"""
    print(f"👤 Authenticated User: {current_user}")

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can submit lessons")

    lesson_data = lesson.dict()
    lesson_data["teacher_name"] = current_user["username"]
    lesson_data["approved"] = False

    inserted = lessons_collection.insert_one(lesson_data)
    return {"message": "Group lesson submitted successfully, pending approval", "lesson_id": str(inserted.inserted_id)}


@router.get("/pending-lessons", response_model=Dict)
def get_pending_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all pending group lessons for the authenticated teacher"""
    print(f"👤 Fetching pending lessons for: {current_user}")

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view their pending lessons")

    pending_lessons = [
        {**lesson, "_id": str(lesson["_id"])}
        for lesson in lessons_collection.find(
            {"teacher_name": current_user["username"], "approved": False}
        )
    ]

    return {
        "message": "Pending group lessons retrieved successfully",
        "pending_lessons": pending_lessons
    }


@router.get("/approved-lessons", response_model=Dict)
def get_approved_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all approved group lessons for the authenticated teacher"""
    print(f"👤 Fetching approved lessons for: {current_user}")

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view their approved lessons")

    approved_lessons = [
        {**lesson, "_id": str(lesson["_id"])}
        for lesson in lessons_collection.find(
            {"teacher_name": current_user["username"], "approved": True}
        )
    ]

    return {
        "message": "Approved group lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.delete("/delete-lesson/{lesson_id}", response_model=dict)
def delete_group_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Delete a group lesson (Only for the lesson owner)"""
    print(f"🗑 Deleting Group Lesson ID: {lesson_id} for User: {current_user['username']}")

    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"]})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to delete")

    lessons_collection.delete_one({"_id": ObjectId(lesson_id)})

    return {"message": "Group lesson deleted successfully"}


@router.put("/update-lesson/{lesson_id}", response_model=dict)
def update_group_lesson(
        lesson_id: str,
        lesson_updates: Dict,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Update a group lesson's details (Only for the lesson owner)"""
    print(f"🛠 Updating Group Lesson ID: {lesson_id} for User: {current_user['username']}")

    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"]})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to update")

    lessons_collection.update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": {k: v for k, v in lesson_updates.items() if k != "_id"}}
    )

    return {"message": "Group lesson updated successfully"}
# @router.get("/dashboard-overview", response_model=Dict)
# def get_dashboard_overview(
#     individual_lessons_collection=Depends(get_individual_lessons_collection),
#     group_lessons_collection=Depends(get_group_lessons_collection),
#     current_user=Depends(get_current_authenticated_user)
# ):
#     """Retrieve dashboard statistics for the authenticated teacher"""
#     print(f"👤 Fetching dashboard overview for: {current_user['username']}")
#
#     # Ensure the user is a teacher
#     if current_user["role"] != "teacher":
#         raise HTTPException(status_code=403, detail="Only teachers can access dashboard overview")
#
#     # ✅ Fetch all approved lessons for the teacher
#     individual_lessons = list(individual_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}))
#     group_lessons = list(group_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}))
#
#     # ✅ Calculate total lessons and total hours
#     total_lessons = len(individual_lessons) + len(group_lessons)
#     total_hours = sum(lesson.get("hours", 0) for lesson in individual_lessons) + sum(lesson.get("hours", 0) for lesson in group_lessons)
#
#     # ✅ Define education levels
#     education_levels = ["ابتدائي", "إعدادي", "ثانوي"]
#
#     # ✅ Fix: Ensure type field exists and is correctly categorized
#     total_individual_hours_by_level = {
#         level: sum(lesson["hours"] for lesson in individual_lessons if lesson.get("education_level") == level )
#         for level in education_levels
#     }
#
#     # ✅ Calculate total group hours by education level
#     total_group_hours_by_level = {
#         level: sum(lesson["hours"] for lesson in group_lessons if lesson.get("education_level") == level )
#         for level in education_levels
#     }
#     return {
#         "message": "Dashboard overview data retrieved successfully",
#         "total_lessons": total_lessons,
#         "total_hours": total_hours,
#         "individual_hours_by_level": total_individual_hours_by_level,
#         "group_hours_by_level": total_group_hours_by_level
#     }




@router.get("/dashboard-overview", response_model=Dict)
def get_dashboard_overview(
    month: int = Query(None, description="Filter lessons by month (1-12)"),
    individual_lessons_collection=Depends(get_individual_lessons_collection),
    group_lessons_collection=Depends(get_group_lessons_collection),
    current_user=Depends(get_current_authenticated_user)
):
    """Retrieve dashboard statistics for the authenticated teacher filtered by month"""
    print(f"👤 Fetching dashboard overview for: {current_user['username']} | Month: {month}")

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access dashboard overview")

    # ✅ Fetch lessons for the selected teacher
    individual_lessons = list(individual_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}))
    group_lessons = list(group_lessons_collection.find({"teacher_name": current_user["username"], "approved": True}))

    # ✅ Fix: Ensure `lesson["date"]` is a string before parsing
    def get_month(lesson):
        if isinstance(lesson["date"], str):  # If already a string
            return datetime.fromisoformat(lesson["date"]).month
        elif isinstance(lesson["date"], datetime):  # If stored as datetime
            return lesson["date"].month
        return None  # Fallback if missing

    # ✅ Filter by month if provided
    if month:
        individual_lessons = [lesson for lesson in individual_lessons if get_month(lesson) == month]
        group_lessons = [lesson for lesson in group_lessons if get_month(lesson) == month]

    # ✅ Calculate total lessons and total hours
    total_lessons = len(individual_lessons) + len(group_lessons)
    total_hours = sum(lesson.get("hours", 0) for lesson in individual_lessons) + sum(lesson.get("hours", 0) for lesson in group_lessons)

    # ✅ Define education levels
    education_levels = ["ابتدائي", "إعدادي", "ثانوي"]

    # ✅ Calculate hours by education level
    total_individual_hours_by_level = {
        level: sum(lesson["hours"] for lesson in individual_lessons if lesson.get("education_level") == level)
        for level in education_levels
    }

    total_group_hours_by_level = {
        level: sum(lesson["hours"] for lesson in group_lessons if lesson.get("education_level") == level)
        for level in education_levels
    }

    return {
        "message": "Dashboard overview data retrieved successfully",
        "total_lessons": total_lessons,
        "total_hours": total_hours,
        "individual_hours_by_level": total_individual_hours_by_level,
        "group_hours_by_level": total_group_hours_by_level
    }