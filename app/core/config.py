import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration settings for the application.
    """
    # Email:
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    VERIFICATION_EXPIRE_HOURS = 2

    # Mongo:
    MONGO_CLUSTER_URL = os.getenv("MONGO_CLUSTER_URL")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")

    # jwt:
    JWT_SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGO_HASH")
    ACCESS_TOKEN_EXPIRE_MINUTES = 3000
    JWT_RESET_SECRET_KEY = os.getenv("JWT_RESET_SECRET_KEY")

config = Config()
