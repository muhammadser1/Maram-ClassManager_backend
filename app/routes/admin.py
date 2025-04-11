from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from datetime import datetime

from app.core.dependencies import get_group_lessons_collection, get_individual_lessons_collection, get_users_collection, \
    role_required

router = APIRouter()


def find_lessons(lessons_collection, filter_query):
    """Retrieve lessons from the database based on a given filter query."""
    lessons = list(
        lessons_collection.find(filter_query, {
            "_id": 1,
            "teacher_name": 1,
            "student_names": 1,
            "student_name": 1,
            "date": 1,
            "hours": 1,
            "education_level": 1,
            "subject": 1,
        })
    )

    for lesson in lessons:
        lesson["_id"] = str(lesson["_id"])

        if "date" in lesson:
            if isinstance(lesson["date"], str):
                try:
                    lesson["date"] = datetime.fromisoformat(lesson["date"]).strftime("%Y-%m-%d")
                except ValueError:
                    pass
            elif isinstance(lesson["date"], datetime):
                lesson["date"] = lesson["date"].strftime("%Y-%m-%d")

    return lessons


def update_lesson_status(lessons_collection, lesson_id: str, approved: bool):
    """Update the approval status of a lesson."""
    try:
        lesson_object_id = ObjectId(lesson_id)
        result = lessons_collection.update_one({"_id": lesson_object_id}, {"$set": {"approved": approved}})

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return {"message": f"Lesson {'approved' if approved else 'rejected'} successfully"}

    except Exception as e:
        print(f"❌ Error updating lesson: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/approved-group-lessons", response_model=dict)
def get_approved_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve all approved group lessons for the admin."""
    print(f"👤 Admin {current_user['username']} fetching approved group lessons")

    approved_lessons = find_lessons(lessons_collection, {"approved": True})

    return {
        "message": "Approved group lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.get("/approved-individual-lessons", response_model=dict)
def get_approved_individual_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve all approved individual lessons for the admin."""
    approved_lessons = find_lessons(lessons_collection, {"approved": True})

    return {
        "message": "Approved individual lessons retrieved successfully",
        "approved_lessons": approved_lessons
    }


@router.get("/pending-individual-lessons", response_model=dict)
def get_pending_individual_lessons(
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve all pending individual lessons for the admin."""
    pending_lessons = find_lessons(lessons_collection, {"approved": False})

    return {
        "message": "Pending individual lessons retrieved successfully",
        "pending_lessons": pending_lessons
    }


@router.post("/approve-individual-lesson/{lesson_id}")
def approve_individual_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Approve an individual lesson."""
    return update_lesson_status(lessons_collection, lesson_id, approved=True)


@router.post("/reject-individual-lesson/{lesson_id}")
def reject_individual_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_individual_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Reject an individual lesson."""
    return update_lesson_status(lessons_collection, lesson_id, approved=False)


@router.get("/pending-group-lessons", response_model=dict)
def get_pending_group_lessons(
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve all pending group lessons for the admin."""
    pending_lessons = find_lessons(lessons_collection, {"approved": False})

    return {
        "message": "Pending group lessons retrieved successfully",
        "pending_lessons": pending_lessons
    }


@router.post("/approve-group-lesson/{lesson_id}")
def approve_group_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Approve a group lesson."""
    return update_lesson_status(lessons_collection, lesson_id, approved=True)


@router.post("/reject-group-lesson/{lesson_id}")
def reject_group_lesson(
        lesson_id: str,
        lessons_collection=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Reject a group lesson."""
    return update_lesson_status(lessons_collection, lesson_id, approved=False)

@router.delete("/admin/delete-lesson/{lesson_id}", response_model=dict)
def admin_delete_lesson(
    lesson_id: str,
    lessons_collection=Depends(get_individual_lessons_collection),
    current_user=Depends(role_required("admin"))
):
    """Admin deletes any lesson (regardless of owner or approval)."""
    result = lessons_collection.delete_one({"_id": ObjectId(lesson_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"message": "Lesson deleted by admin successfully"}

@router.get("/student-stats", response_model=dict)
def get_student_stats(
        month: str = Query(..., description="Month in YYYY-MM format"),
        token: str = Query(..., description="Access token"),
        individual_lessons=Depends(get_individual_lessons_collection),
        group_lessons=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve student statistics filtered by a given month (YYYY-MM)."""

    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    student_stats = {}

    individual_lessons_list = list(individual_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}
        ]
    }))

    group_lessons_list = list(group_lessons.find({
        "approved": True,
        "$or": [
            {"$expr": {"$regexMatch": {
                "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                "regex": f"^{month}"
            }}},
            {"date": {"$regex": f"^{month}"}}
        ]
    }))

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


@router.get("/teacher-individual-stats", response_model=dict)
def get_teacher_individual_stats(
        month: str,
        individual_lessons=Depends(get_individual_lessons_collection),
        group_lessons=Depends(get_group_lessons_collection),
        current_user=Depends(role_required("admin"))
):
    """Retrieve statistics for all teachers' individual and group lessons in the given month."""

    try:
        datetime.strptime(month, "%Y-%m")  # Validate date format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    teacher_stats = {}

    # ✅ Fetch lessons for the given month
    def fetch_lessons(collection):
        return list(collection.find({
            "approved": True,
            "$or": [
                {"$expr": {"$regexMatch": {
                    "input": {"$dateToString": {"format": "%Y-%m", "date": {"$toDate": "$date"}}},
                    "regex": f"^{month}"
                }}},
                {"date": {"$regex": f"^{month}"}}  # Handle string dates
            ]
        }))

    individual_lessons_list = fetch_lessons(individual_lessons)
    group_lessons_list = fetch_lessons(group_lessons)

    # ✅ Process Individual Lessons
    for lesson in individual_lessons_list:
        teacher_name = lesson.get("teacher_name", "Unknown Teacher")
        education_level = lesson.get("education_level", "Unknown Level")
        hours = lesson.get("hours", 0)

        if teacher_name not in teacher_stats:
            teacher_stats[teacher_name] = {
                "teacher_name": teacher_name,
                "total_individual_hours": 0,
                "total_group_hours": 0,
                "individual_hours_by_education_level": {},
                "group_hours_by_education_level": {},
            }

        teacher_stats[teacher_name]["total_individual_hours"] += hours
        teacher_stats[teacher_name]["individual_hours_by_education_level"].setdefault(education_level, 0)
        teacher_stats[teacher_name]["individual_hours_by_education_level"][education_level] += hours

    # ✅ Process Group Lessons
    for lesson in group_lessons_list:
        teacher_name = lesson.get("teacher_name", "Unknown Teacher")
        education_level = lesson.get("education_level", "Unknown Level")
        hours = lesson.get("hours", 0)

        if teacher_name not in teacher_stats:
            teacher_stats[teacher_name] = {
                "teacher_name": teacher_name,
                "total_individual_hours": 0,
                "total_group_hours": 0,
                "individual_hours_by_education_level": {},
                "group_hours_by_education_level": {},
            }

        teacher_stats[teacher_name]["total_group_hours"] += hours
        teacher_stats[teacher_name]["group_hours_by_education_level"].setdefault(education_level, 0)
        teacher_stats[teacher_name]["group_hours_by_education_level"][education_level] += hours

    return {
        "message": "Teacher individual lesson stats retrieved successfully",
        "teachers": list(teacher_stats.values())
    }
