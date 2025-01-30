from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timezone, timedelta
from app.core.config import config
import random
import string

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Verifies and decodes a JWT token.
    Returns the user data if valid, otherwise raises an HTTP exception.
    """
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        if "email" not in payload or "role" not in payload or "username" not in payload or "exp" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token format")

        if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token has expired")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token: dict = Depends(verify_token)) -> dict:
    """
    Extracts and returns user information from JWT token.
    """
    return {
        "email": token["email"],
        "username": token["username"],
        "role": token["role"]
    }


def create_reset_token(email: str):
    """Generate a password reset token with a short expiration."""
    expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, config.JWT_RESET_SECRET_KEY, algorithm=config.ALGORITHM)


def verify_reset_token(token: str):
    """Verify a password reset token and return the email if valid."""
    try:
        payload = jwt.decode(token, config.JWT_RESET_SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload["sub"]
    except JWTError:
        return None


def generate_token(length: int = 40) -> str:
    """Generate a secure random token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))