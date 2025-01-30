import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import random
import string

from app.core.config import config


def send_email(subject: str, body: str, to_email: str):
    """Generic function to send an email."""
    sender_email = config.EMAIL_USER
    password = config.EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")


def send_verification_email(to_email: str, token: str, name: str):
    """Send an email verification link after user signup."""
    subject = "Verify Your Account"
    body = f"""
    Dear {name},

    Thank you for signing up! Please verify your email by clicking the link below:

    http://localhost:5173/verify-email?token={token}

    This link will expire in 24 hours.

    If you did not sign up, please ignore this email.

    Regards,
    Your Institute
    """
    send_email(subject, body, to_email)



def send_reset_email(to_email: str, token: str, name: str):
    """Send a password reset link via email."""
    subject = "Password Reset Request"
    body = f"""
    Dear {name},

    We received a request to reset your password. Click the link below:

    http://localhost:5173/reset-password?token={token}

    If you did not request this, please ignore the email.

    Regards,
    Your Institute
    """
    send_email(subject, body, to_email)