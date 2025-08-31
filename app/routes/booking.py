from datetime import datetime
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from apscheduler.triggers.interval import IntervalTrigger

from bson import ObjectId

from app.core.database import mongo_db
from app.models.booking import Booking
from app.core.dependencies import get_student_bookings_collection, role_required
from app.utils.send_email_with_attachments import export_to_csv_memory, send_email_with_attachment
from app.core.config import config

router = APIRouter()


# ---------- Helpers ----------
def _todays_iso_utc() -> str:
    return datetime.utcnow().date().isoformat()

def _stringify_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def _coerce_date_or_today(date_str: Optional[str]) -> str:
    """
    Return a YYYY-MM-DD string.
    - If date_str is None/empty -> use today's UTC date.
    - If provided -> validate format YYYY-MM-DD or raise 400.
    """
    if not date_str:
        return _todays_iso_utc()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


# ---------- Routes ----------

# 1) Create booking
@router.post("/", response_model=dict)
def create_booking(
    booking_data: dict,
    bookings_collection=Depends(get_student_bookings_collection),
):
    """
    Create a booking.
    Expected payload (key fields):
      - phone, subject, ageLevel, lessonDate (YYYY-MM-DD), lessonTime (HH:MM 24h), hours (float)
      - students: List[str]  (>=1 for individual, >=2 for group)
      - lessonType: "individual" | "group" (default: individual)
      - status: "pending" | "approved" | "completed" | "cancelled" (default: pending)
      - parentName: Optional[str]
      - notes: Optional[str]
    """
    return Booking.create_booking(booking_data, bookings_collection)


# 2) Update booking status
@router.patch("/{booking_id}/status", response_model=dict)
def update_booking_status(
    booking_id: str,
    payload: dict,   # expects {"status": "approved"} etc.
    bookings_collection=Depends(get_student_bookings_collection),
    current_user=Depends(role_required("admin")),
):
    new_status = payload.get("status")
    if new_status not in ["pending", "approved", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    try:
        obj_id = ObjectId(booking_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking_id")

    updated = bookings_collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": {"status": new_status}},
        return_document=True,  # assumes your pymongo helper handles ReturnDocument
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found")

    _stringify_id(updated)
    return {"message": "Status updated", "booking": updated}


# 3) Bookings created on a date (default: today UTC)
@router.get("/today/bookings", response_model=List[dict])
def get_bookings_by_date(
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD (UTC). Omit for today."),
    bookings_collection=Depends(get_student_bookings_collection),
    current_user=Depends(role_required("admin")),
):
    target = _coerce_date_or_today(date)
    items = list(bookings_collection.find({"bookingDate": target}))
    return [_stringify_id(x) for x in items]


# 4) Lessons scheduled on a date (default: today UTC)
@router.get("/today/lessons", response_model=List[dict])
def get_lessons_by_date(
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD (UTC). Omit for today."),
    bookings_collection=Depends(get_student_bookings_collection),
    current_user=Depends(role_required("admin")),
):
    target = _coerce_date_or_today(date)
    items = list(bookings_collection.find({"lessonDate": target}))
    return [_stringify_id(x) for x in items]


# ---------- Email Export ----------

def process_today_bookings():
    today = _todays_iso_utc()
    coll = mongo_db.student_bookings_collection

    bookings_today = list(coll.find({"bookingDate": today}))
    lessons_today = list(coll.find({"lessonDate": today}))

    for b in bookings_today:
        _stringify_id(b)
    for l in lessons_today:
        _stringify_id(l)

    # UPDATED: headers reflect new Booking model (parentName instead of first/last name)
    headers = [
        "parentName", "phone", "subject", "ageLevel",
        "lessonDate", "lessonTime", "hours", "notes",
        "lessonType", "students", "status", "bookingDate"
    ]

    def normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
        d = dict(doc)
        # stringify list of students
        if isinstance(d.get("students"), list):
            d["students"] = "; ".join([str(s) for s in d["students"]])
        # ensure all headers exist (missing -> empty string)
        for h in headers:
            d.setdefault(h, "")
        # keep only expected columns & order
        return {h: d.get(h, "") for h in headers}

    bookings_csv = export_to_csv_memory([normalize(x) for x in bookings_today], headers)
    lessons_csv = export_to_csv_memory([normalize(x) for x in lessons_today], headers)

    send_email_with_attachment(
        subject=f"Daily Report {today}",
        body=f"Attached are today's bookings (created today) and lessons (scheduled today).",
        to_email=config.EMAIL_TO,
        attachments=[
            (f"bookings_{today}.csv", bookings_csv),
            (f"lessons_{today}.csv", lessons_csv),
        ],
    )


# ---------- Scheduler ----------

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=timezone("Asia/Jerusalem"))

    # Daily at 10:00 Asia/Jerusalem
    scheduler.add_job(
        process_today_bookings,
        trigger=CronTrigger(hour=10, minute=0),
        id="daily_report_10am",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # For testing: every 2 minutes
    # scheduler.add_job(
    #     process_today_bookings,
    #     trigger=IntervalTrigger(minutes=2),
    #     id="test_report_every_2min",
    #     replace_existing=True,
    #     max_instances=1,
    #     coalesce=True,
    # )

    scheduler.start()
