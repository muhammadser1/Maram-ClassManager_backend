from fastapi import Depends, HTTPException
from app.core.database import mongo_db
from app.core.security import get_current_user


def get_database():
    """Dependency to get the database connection instance."""
    return mongo_db.db


# def get_users_collection(db=Depends(get_database)):
#     """Dependency to get the users collection."""
#     return db["users"]
#
#
# def get_lessons_collection(db=Depends(get_database)):
#     """Dependency to get the lessons collection."""
#     return db.lessons_collection
#
#
# def get_supports_collection(db=Depends(get_database)):
#     """Dependency to get the support collection."""
#     return db.supports_collection

def get_collection(collection_name: str):
    """Generic function to get any MongoDB collection."""

    def _get_collection(db=Depends(get_database)):
        return db[collection_name]

    return _get_collection


get_users_collection = get_collection("Users")
get_lessons_collection = get_collection("Lessons")
get_students_collection = get_collection("Students")


def get_current_authenticated_user(user: dict = Depends(get_current_user)):
    """Dependency to ensure the user is authenticated."""
    return user


def role_required(required_role: str):
    """
    Dependency for enforcing role-based access.
    """

    def _role_checker(user: dict = Depends(get_current_user)):
        if user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Access denied")
        return user

    return _role_checker
