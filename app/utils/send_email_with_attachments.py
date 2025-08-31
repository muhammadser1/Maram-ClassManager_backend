import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from app.core.config import config


def export_to_csv_memory(data, headers):
    """Export MongoDB data to CSV (in-memory, no file writes)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for row in data:
        safe_row = {h: row.get(h, "") for h in headers}  # keep only allowed keys
        writer.writerow(safe_row)
    buf.seek(0)
    return buf.getvalue()  # return string CSV data


def send_email_with_attachment(subject: str, body: str, to_email: str, attachments: list[tuple[str, str]]):
    """
    Send an email with CSV (or any file-like) attachments.
    attachments: list of (filename, file_content) tuples
    """
    sender_email = config.EMAIL_USER
    password = config.EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Add attachments (in-memory)
    for filename, content in attachments:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(content.encode("utf-8"))  # encode string to bytes
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print(f"📧 Email sent successfully to {to_email} with attachments: {[fn for fn, _ in attachments]}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
