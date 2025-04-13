from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from bson import ObjectId

from app.core.dependencies import get_student_payments_collection, role_required

router = APIRouter()


@router.post("/", response_model=dict)
def add_student_payment(
    name: str = Query(...),
    cost: int = Query(...),
    date: str = Query(...),
    payments_collection=Depends(get_student_payments_collection),
    current_user=Depends(role_required("admin"))
):
    """Add a student payment."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    payment = {
        "name": name.strip(),
        "cost": cost,
        "date": date,
    }

    result = payments_collection.insert_one(payment)
    return {"message": "✅ Payment added successfully", "payment_id": str(result.inserted_id)}


@router.get("/", response_model=dict)
def get_payments_by_month(
    month: str = Query(..., description="Month in YYYY-MM"),
    payments_collection=Depends(get_student_payments_collection),
    current_user=Depends(role_required("admin"))
):
    """Get all student payments for a specific month."""
    try:
        datetime.strptime(month, "%Y-%m")  # Validate month
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    payments = list(payments_collection.find({
        "date": {"$regex": f"^{month}"}
    }))

    for p in payments:
        p["_id"] = str(p["_id"])

    return {"payments": payments}
