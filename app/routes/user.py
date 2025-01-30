from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import verify_password, hash_password
from app.core.config import config
from app.core.dependencies import get_users_collection

from app.core.security import create_access_token, create_reset_token, verify_reset_token, generate_token
from app.models.admin import Admin
from app.models.base_user import User
from app.models.teacher import Teacher
from app.schemas.user import UserBase, Role, UserLogin, ForgotPasswordRequest, ResetPasswordRequest
from app.utils.email_utils import send_verification_email, send_reset_email

router = APIRouter()


@router.post("/signin")
def signin(user: UserLogin, users_collection=Depends(get_users_collection)):
    """Authenticate a user and return a JWT token, only if verified."""
    existing_user = users_collection.find_one({"username": user.username})

    if not existing_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if not existing_user.get("verified", False):  # ✅ Check if user is verified
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email before logging in.")

    token = create_access_token({"sub": existing_user["username"], "role": existing_user["role"]})

    return {"access_token": token, "token_type": "bearer"}


@router.post("/signup")
def signup(user: UserBase, users_collection=Depends(get_users_collection)):
    """Register a new user with email verification and expiration."""
    existing_user = users_collection.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email or username already exists")

    verification_token = generate_token()
    expiration_time = datetime.utcnow() + timedelta(hours=config.VERIFICATION_EXPIRE_HOURS)

    try:
        role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    hashed_password = hash_password(user.password.get_secret_value())

    if role == Role.ADMIN:
        new_user = Admin(
            user.username, user.email, hashed_password,
            birthday=user.birthday,
            verified=False, verification_token=verification_token,
            verification_expiry=expiration_time
        )
    elif role == Role.TEACHER:
        new_user = Teacher(
            user.username, user.email, hashed_password,
            birthday=user.birthday,
            verified=False, verification_token=verification_token,
            verification_expiry=expiration_time
        )

    new_user.save(users_collection)
    send_verification_email(user.email, verification_token, user.username)

    return {"message": "User registered successfully. Please check your email to verify your account."}


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, users_collection=Depends(get_users_collection)):
    """Generate a password reset token and send it via email."""
    user = users_collection.find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=400, detail="User with this email not found")

    reset_token = create_reset_token(user["email"])

    send_reset_email(user["email"], reset_token, user["username"])

    return {"message": "A password reset link has been sent to your email."}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, users_collection=Depends(get_users_collection)):
    """Verify the reset token and allow the user to set a new password."""
    email = verify_reset_token(request.token)

    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    hashed_password = hash_password(request.new_password)

    users_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

    return {"message": "Password reset successful"}


@router.get("/verify-email")
def verify_email(token: str, users_collection=Depends(get_users_collection)):
    """Confirm user email verification with expiration check."""
    user = users_collection.find_one({"verification_token": token})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if user.get("verification_expiry") and datetime.utcnow() > user["verification_expiry"]:
        raise HTTPException(status_code=400, detail="Verification link has expired. Request a new one.")

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"verified": True}, "$unset": {"verification_token": "", "verification_expiry": ""}}
    )

    return {"message": "Email verified successfully! You can now log in."}


@router.post("/resend-verification")
def resend_verification(email: str, users_collection=Depends(get_users_collection)):
    """Resend a new verification email if the old one expired."""
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.get("verified"):
        raise HTTPException(status_code=400, detail="User is already verified")

    # Generate a new token
    new_verification_token = generate_token()
    expiration_time = datetime.utcnow() + timedelta(hours=config.VERIFICATION_EXPIRE_HOURS)

    # Update user with a new token and expiration time
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"verification_token": new_verification_token, "verification_expiry": expiration_time}}
    )

    send_verification_email(user["email"], new_verification_token, user["username"])

    return {"message": "A new verification link has been sent to your email."}
