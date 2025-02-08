from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.core.dependencies import get_group_lessons_collection, get_current_authenticated_user, \
    get_individual_lessons_collection, get_users_collection

router = APIRouter()


@router.get("/approved-group-lessons", response_model=dict)
def get_approved_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all approved group lessons for the admin."""
    print(f"👤 Admin {current_user['username']} fetching approved group lessons")

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view approved group lessons")

    approved_lessons = list(lessons_collection.find(
        {"approved": True},
        {"_id": 0}
    ))

    return {
        "message": "Approved group lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.get("/approved-individual-lessons", response_model=dict)
def get_approved_individual_lessons(lessons_collection=Depends(get_individual_lessons_collection),
                                    current_user=Depends(get_current_authenticated_user)):
    """Retrieve all approved individual lessons for the admin."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view approved individual lessons")

    approved_lessons = list(lessons_collection.find(
        {"approved": True},
        {"_id": 0}
    ))

    return {
        "message": "Approved individual lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.get("/pending-individual-lessons", response_model=dict)
def get_pending_individual_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Retrieve all pending individual lessons for the admin."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view pending individual lessons")

    pending_lessons = list(lessons_collection.find(
        {"approved": False},
        {"_id": 1, "teacher_name": 1, "student_name": 1, "date": 1, "hours": 1}  # Include _id
    ))

    # Convert ObjectId to string so frontend gets it
    for lesson in pending_lessons:
        lesson["_id"] = str(lesson["_id"])

    return {
        "message": "Pending individual lessons retrieved successfully",
        "pending_lessons": pending_lessons
    }


@router.post("/approve-individual-lesson/{lesson_id}")
def approve_individual_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Approve an individual lesson."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can approve lessons")

    try:
        lesson_object_id = ObjectId(lesson_id)
        result = lessons_collection.update_one({"_id": lesson_object_id}, {"$set": {"approved": True}})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return {"message": "Lesson approved successfully"}

    except Exception as e:
        print(f"❌ Error updating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/reject-individual-lesson/{lesson_id}")
def reject_individual_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(get_current_authenticated_user)
):
    """Reject an individual lesson."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reject lessons")

    try:
        lesson_object_id = ObjectId(lesson_id)
        result = lessons_collection.delete_one({"_id": lesson_object_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return {"message": "Lesson rejected successfully"}

    except Exception as e:
        print(f"❌ Error deleting lesson: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/pending-group-lessons", response_model=dict)
def get_pending_group_lessons(lessons_collection=Depends(get_group_lessons_collection),
                              current_user=Depends(get_current_authenticated_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view pending group lessons")

    pending_lessons = list(lessons_collection.find({"approved": False}))
    for lesson in pending_lessons:
        lesson["_id"] = str(lesson["_id"])

    return {"message": "Pending group lessons retrieved", "pending_lessons": pending_lessons}


@router.post("/approve-group-lesson/{lesson_id}")
def approve_group_lesson(lesson_id: str, lessons_collection=Depends(get_group_lessons_collection),
                         current_user=Depends(get_current_authenticated_user)):
    lesson_object_id = ObjectId(lesson_id)
    result = lessons_collection.update_one({"_id": lesson_object_id}, {"$set": {"approved": True}})
    return {"message": "Group lesson approved successfully"} if result.matched_count else HTTPException(status_code=404,
                                                                                                        detail="Lesson not found")


@router.post("/reject-group-lesson/{lesson_id}")
def reject_group_lesson(lesson_id: str, lessons_collection=Depends(get_group_lessons_collection),
                        current_user=Depends(get_current_authenticated_user)):
    lesson_object_id = ObjectId(lesson_id)
    result = lessons_collection.delete_one({"_id": lesson_object_id})
    return {"message": "Group lesson rejected successfully"} if result.deleted_count else HTTPException(status_code=404,
                                                                                                        detail="Lesson not found")


from datetime import datetime


@router.get("/teacher-stats", response_model=dict)
def get_teacher_stats(
        month: str,
        individual_lessons=Depends(get_individual_lessons_collection),
        group_lessons=Depends(get_group_lessons_collection)
):
    """Retrieve teacher statistics filtered by a given month (YYYY-MM), grouped by teacher_name and education_level.
       Only approved lessons are included.
    """

    try:
        datetime.strptime(month, "%Y-%m")  # Validate date format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    teacher_stats = {}

    # If no approved lessons exist, return early
    if individual_lessons.count_documents({"approved": True}) == 0 and group_lessons.count_documents(
            {"approved": True}) == 0:
        return {
            "message": "No approved lessons found",
            "teachers": []
        }

    # Fetch Approved Individual Lessons (Handling both ISODate and String Dates)
    lessons = list(individual_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}  # Handle string dates
        ]
    }))

    # Fetch Approved Group Lessons (Handling both ISODate and String Dates)
    group_lessons_list = list(group_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}  # Handle string dates
        ]
    }))

    for lesson in lessons:
        teacher_name = lesson.get("teacher_name", "Unknown Teacher")
        education_level = lesson.get("education_level", "Unknown Level")

        if teacher_name not in teacher_stats:
            teacher_stats[teacher_name] = {
                "teacher_name": teacher_name,
                "total_individual_hours": 0,
                "total_group_hours": 0,
                "education_levels_individual": {},
                "education_levels_group": {}
            }

        if education_level not in teacher_stats[teacher_name]["education_levels_individual"]:
            teacher_stats[teacher_name]["education_levels_individual"][education_level] = 0

        teacher_stats[teacher_name]["education_levels_individual"][education_level] += lesson.get("hours", 0)
        teacher_stats[teacher_name]["total_individual_hours"] += lesson.get("hours", 0)

    for lesson in group_lessons_list:
        teacher_name = lesson.get("teacher_name", "Unknown Teacher")
        education_level = lesson.get("education_level", "Unknown Level")

        if teacher_name not in teacher_stats:
            teacher_stats[teacher_name] = {
                "teacher_name": teacher_name,
                "total_individual_hours": 0,
                "total_group_hours": 0,
                "education_levels_individual": {},
                "education_levels_group": {}
            }

        if education_level not in teacher_stats[teacher_name]["education_levels_group"]:
            teacher_stats[teacher_name]["education_levels_group"][education_level] = 0

        teacher_stats[teacher_name]["education_levels_group"][education_level] += lesson.get("hours", 0)
        teacher_stats[teacher_name]["total_group_hours"] += lesson.get("hours", 0)
    students = {}

    for lesson in lessons + group_lessons_list:
        student_name = lesson.get("student_name", "Unknown Student")
        education_level = lesson.get("education_level", "Unknown Level")

        if student_name not in students:
            students[student_name] = {
                "student_name": student_name,
                "total_hours": 0,
                "education_level": education_level
            }

        students[student_name]["total_hours"] += lesson.get("hours", 0)

    return {
        "message": "Teacher statistics retrieved successfully",
        "teachers": list(teacher_stats.values()),
        "students": list(students.values())
    }


@router.get("/student-stats", response_model=dict)
def get_student_stats(
        month: str,
        individual_lessons=Depends(get_individual_lessons_collection),
        group_lessons=Depends(get_group_lessons_collection)
):
    """Retrieve student statistics filtered by a given month (YYYY-MM), calculating both individual and group hours."""

    try:
        datetime.strptime(month, "%Y-%m")  # Validate date format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    student_stats = {}

    # Fetch Approved Individual Lessons
    individual_lessons_list = list(individual_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}  # Handle string dates
        ]
    }))

    # Fetch Approved Group Lessons
    group_lessons_list = list(group_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}  # Handle string dates
        ]
    }))

    # Process Individual Lessons
    for lesson in individual_lessons_list:
        student_name = lesson.get("student_name", "Unknown Student")
        education_level = lesson.get("education_level", "Unknown Level")

        if student_name not in student_stats:
            student_stats[student_name] = {
                "student_name": student_name,
                "total_individual_hours": 0,
                "total_group_hours": 0,
                "education_level": education_level
            }

        student_stats[student_name]["total_individual_hours"] += lesson.get("hours", 0)

    # Process Group Lessons
    for lesson in group_lessons_list:
        student_names = lesson.get("student_names", [])
        education_level = lesson.get("education_level", "Unknown Level")

        for student_name in student_names:
            if student_name not in student_stats:
                student_stats[student_name] = {
                    "student_name": student_name,
                    "total_individual_hours": 0,
                    "total_group_hours": 0,
                    "education_level": education_level
                }

            student_stats[student_name]["total_group_hours"] += lesson.get("hours", 0)

    return {
        "message": "Student statistics retrieved successfully",
        "students": list(student_stats.values())
    }
