
from __future__ import annotations

import json
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from dotenv import load_dotenv

# Import the agent from unravel.py
from unravel import extract_founder_info, scrape_unravel_profiles

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SENDER_EMAIL = "nileshpataskars@gmail.com"
SENDER_NAME = "Nilesh Pataskar"
RESUME_PATH = Path(__file__).parent / "Nilesh Pataskar Resume.pdf"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------------------------------------------------------------------
# Email Content
# ---------------------------------------------------------------------------

SUBJECT = "Apply | DSPy | KillJOY"

EMAIL_BODY = """\
Hi,

I am writing to apply for the Software Development Engineer (SDE) role at Unravel.tech.

I am a Full Stack Developer with roughly three years of experience, specializing in technologies like TypeScript (React), .NET, and SQL. I am comfortable working in both Python and TypeScript and am passionate about solving real engineering problems, with a focus on clean architecture.

I have attached my resume below

Thank you for considering my application, and I would be thrilled to hear from you.

Thank you for considering my application, I'll be thrilled to hearing from you

Thanks,
Nilesh Pataskar
(with assistance from ChatGPT)

"""


def send_application_email(recipient: str) -> None:
    """
    Send an application email with resume attached.

    Parameters
    ----------
    recipient : str
        The recipient's email address.
    """

    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not app_password:
        print(
            "Error: GMAIL_APP_PASSWORD environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not RESUME_PATH.exists():
        print(f"Error: Resume not found at {RESUME_PATH}", file=sys.stderr)
        sys.exit(1)

    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = recipient
    msg["Subject"] = SUBJECT

    msg.attach(MIMEText(EMAIL_BODY, "plain"))

    with open(RESUME_PATH, "rb") as f:
        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename={RESUME_PATH.name}",
        )
        msg.attach(attachment)

    try:
        print(f"Connecting to {SMTP_SERVER}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, app_password)
            server.send_message(msg)
        print(f"✅ Email sent successfully to {recipient}")
    except smtplib.SMTPAuthenticationError:
        print(
            "Error: Authentication failed.",
            file=sys.stderr,
        )
        sys.exit(1)
    except smtplib.SMTPException as exc:
        print(f"SMTP error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Full pipeline:
    1. Use the LLM agent to extract the founder's email from profiles
    2. Send the application email to that founder
    """

    print("🌐 Step 1: Scraping unravel.tech for founder profiles...")
    profiles = scrape_unravel_profiles()
    print(f"   Fetched {len(profiles)} characters of content.\n")

    print("🤖 Step 2: Extracting founder info with LLM agent...")
    result = extract_founder_info(profiles)

    founder_name = result.get("founder_name")
    recipient = result.get("email")

    if not founder_name or not recipient:
        print("Error: Could not extract founder info.", file=sys.stderr)
        sys.exit(1)

    print(f"   Found: {founder_name}")
    print(f"   Email: {recipient}")
    print()

    print(f"📧 Step 2: Ready to send application email:")
    print(f"   From:    {SENDER_EMAIL}")
    print(f"   To:      {recipient}")
    print(f"   Subject: {SUBJECT}")
    print(f"   Resume:  {RESUME_PATH.name}")
    print()

    confirm = input("Send this email? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    send_application_email(recipient)

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
