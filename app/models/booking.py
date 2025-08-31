# app/models/booking.py
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any

LessonStatus = Literal["pending", "approved", "completed", "cancelled"]
LessonType = Literal["individual", "group"]

class Booking:
    """
    Booking model:
    - parentName (optional), phone, subject, ageLevel
    - lessonDate (YYYY-MM-DD), lessonTime (HH:MM 24h), hours (float), notes
    - lessonType: "individual" | "group"
    - students: list of names (>=1 for individual, >=2 for group)
    - status: "pending" | "approved" | "completed" | "cancelled"
    - bookingDate (auto from created_at)
    - created_at (UTC)
    """

    def __init__(
        self,
        phone: str,
        subject: str,
        ageLevel: str,
        lessonDate: str,
        lessonTime: str,
        hours: float,
        students: List[str],
        notes: Optional[str] = None,

        parentName: Optional[str] = None,
        lessonType: LessonType = "individual",
        status: LessonStatus = "pending",

        bookingDate: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        # main fields
        self.parentName = parentName
        self.phone = phone
        self.subject = subject
        self.ageLevel = ageLevel
        self.lessonDate = lessonDate
        self.lessonTime = lessonTime
        self.hours = float(hours)
        self.notes = notes

        # set lessonType first, then normalize+validate students
        self.lessonType = lessonType
        self.students = [s.strip() for s in (students or []) if s and s.strip()]

        if self.lessonType == "group" and len(self.students) < 2:
            raise ValueError("Group lessons must have at least two students.")
        if self.lessonType == "individual" and len(self.students) != 1:
            raise ValueError("Individual lessons must have exactly one student.")

        # status & system
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.bookingDate = bookingDate or self.created_at.date().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parentName": self.parentName,
            "phone": self.phone,
            "subject": self.subject,
            "ageLevel": self.ageLevel,
            "lessonDate": self.lessonDate,
            "lessonTime": self.lessonTime,
            "hours": self.hours,
            "notes": self.notes,
            "lessonType": self.lessonType,
            "students": self.students,
            "status": self.status,
            "bookingDate": self.bookingDate,
            "created_at": self.created_at,
        }

    # ---------- CRUD helpers (ADD THESE BACK) ----------

    @staticmethod
    def create_booking(booking_data: dict, student_bookings_collection):
        """
        Insert a new booking into MongoDB.
        Expects: phone, subject, ageLevel, lessonDate, lessonTime, hours,
                 lessonType, students (frontend must provide),
                 optional: parentName, notes, status
        """
        # defaults (backend still sane even if frontend doesn't send them)
        booking_data.setdefault("lessonType", "individual")
        booking_data.setdefault("status", "pending")

        # Instantiate (will validate students vs lessonType)
        booking = Booking(**booking_data)

        # Insert
        result = student_bookings_collection.insert_one(booking.to_dict())
        return {
            "message": "Booking created successfully",
            "bookingId": str(result.inserted_id),
        }

    @staticmethod
    def get_all(student_bookings_collection, status: Optional[LessonStatus] = None, lessonType: Optional[LessonType] = None):
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if lessonType:
            query["lessonType"] = lessonType

        bookings = list(student_bookings_collection.find(query).sort([("lessonDate", 1), ("lessonTime", 1)]))
        for b in bookings:
            b["_id"] = str(b["_id"])
        return bookings

    @staticmethod
    def update_status(booking_id: str, new_status: LessonStatus, student_bookings_collection):
        from bson import ObjectId
        student_bookings_collection.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": new_status}})
        return {"message": "Status updated", "bookingId": booking_id, "status": new_status}
