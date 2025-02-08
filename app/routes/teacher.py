from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_individual_lessons_collection, get_current_authenticated_user, \
    get_users_collection
from app.schemas.Lesson import IndividualLessonBase
from datetime import datetime

router = APIRouter()


@router.post("/submit", response_model=dict)
def submit_lesson(
        lesson: IndividualLessonBase,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Submit a new lesson (Pending Approval)"""
    print(f"👤 Authenticated User: {current_user}")  # Debugging

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can submit lessons")

    lesson_data = lesson.dict()
    lesson_data["teacher_name"] = current_user["username"]
    lesson_data["approved"] = False

    lessons_collection.insert_one(lesson_data)

    return {"message": "Lesson submitted successfully, pending approval"}


@router.get("/pending-lessons", response_model=dict)
def get_pending_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all pending lessons for the authenticated teacher."""
    print(f"👤 Fetching pending lessons for: {current_user}")

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view their pending lessons")

    # ✅ Fetch lessons & convert `_id` to string
    pending_lessons = [
        {**lesson, "_id": str(lesson["_id"])}
        for lesson in lessons_collection.find(
            {"teacher_name": current_user["username"], "approved": False}
        )
    ]

    return {
        "message": "Pending lessons retrieved successfully",
        "pending_lessons": pending_lessons
    }


@router.get("/approved-lessons", response_model=dict)
def get_approved_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all approved lessons for the authenticated teacher."""
    print(f"👤 Fetching approved lessons for: {current_user}")  # Debugging

    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view their approved lessons")

    # Fetch all approved lessons for the current teacher
    approved_lessons = list(lessons_collection.find(
        {"teacher_name": current_user["username"], "approved": True},
        {"_id": 0}  # Exclude MongoDB's _id field from response
    ))

    return {
        "message": "Approved lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.delete("/delete-lesson/{lesson_id}", response_model=dict)
def delete_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Delete a lesson (Only for the lesson owner)"""
    print(f"🗑 Deleting Lesson ID: {lesson_id} for User: {current_user['username']}")

    # ✅ Check if the lesson exists and belongs to the current teacher
    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"]})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to delete")

    # ✅ Delete the lesson
    lessons_collection.delete_one({"_id": ObjectId(lesson_id)})

    return {"message": "Lesson deleted successfully"}


@router.put("/update-lesson/{lesson_id}", response_model=dict)
def update_lesson(
        lesson_id: str,  # ✅ Accept lesson ID as a parameter
        lesson_updates: dict,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Update a lesson's details (Only for the lesson owner)"""
    print(f"🛠 Updating Lesson ID: {lesson_id} for User: {current_user['username']}")

    # ✅ Check if the lesson exists and belongs to the current teacher
    lesson = lessons_collection.find_one({"_id": ObjectId(lesson_id), "teacher_name": current_user["username"]})

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or not authorized to update")

    # ✅ Perform update (Exclude `_id` to prevent errors)
    lessons_collection.update_one(
        {"_id": ObjectId(lesson_id)},
        {"$set": {k: v for k, v in lesson_updates.items() if k != "_id"}}
    )

    return {"message": "Lesson updated successfully"}


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







