from fastapi import Depends, HTTPException
from app.core.database import mongo_db
from app.core.security import get_current_user


def get_database():
    """ Dependency to get the database connection instance. """
    return mongo_db.db


def get_collection(collection_name: str):
    """ Generic function to get any MongoDB collection. """

    def _get_collection(db=Depends(get_database)):
        return db[collection_name]

    return _get_collection


# Optimized Collection Dependencies
get_users_collection = get_collection("Users")
get_individual_lessons_collection = get_collection("IndividualLessons")
get_group_lessons_collection = get_collection("GroupLessons")
get_student_payments_collection = get_collection("StudentPayments")


def get_current_authenticated_user(user: dict = Depends(get_current_user)):
    """ Dependency to ensure the user is authenticated. """
    return user


def role_required(*roles: str):
    """
    Dependency for enforcing role-based access.
    Supports multiple roles (e.g., `role_required("admin", "teacher")`).
    """

    def _role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return user

    return _role_checker
