from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

IMAP_HOSTS = {
    "gmail": "imap.gmail.com",
    "yahoo": "imap.mail.yahoo.com",
}


@dataclass(frozen=True)
class Config:
    provider: str
    email_address: str
    app_password: str
    target_folder: str
    dry_run: bool
    max_messages: int
    imap_host: str
    applied_jobs_file: str
    sender_blocklist_file: str


def load_config() -> Config:
    load_dotenv()

    provider = os.getenv("EMAIL_PROVIDER", "").lower()
    if provider not in IMAP_HOSTS:
        raise ValueError(
            f"EMAIL_PROVIDER must be one of {list(IMAP_HOSTS.keys())}, got: {repr(provider)}"
        )

    email_address = os.getenv("EMAIL_ADDRESS", "")
    if not email_address:
        raise ValueError("EMAIL_ADDRESS is required in .env")

    app_password = os.getenv("EMAIL_APP_PASSWORD", "")
    if not app_password:
        raise ValueError("EMAIL_APP_PASSWORD is required in .env")

    target_folder = os.getenv("TARGET_FOLDER", "Job Applications/Responses")
    dry_run = os.getenv("DRY_RUN", "true").lower() != "false"
    max_messages = int(os.getenv("MAX_MESSAGES", "50"))
    applied_jobs_file = os.getenv("APPLIED_JOBS_FILE", "applied_jobs.xlsx")
    sender_blocklist_file = os.getenv("SENDER_BLOCKLIST_FILE", "sender_blocklist.txt")

    return Config(
        provider=provider,
        email_address=email_address,
        app_password=app_password,
        target_folder=target_folder,
        dry_run=dry_run,
        max_messages=max_messages,
        imap_host=IMAP_HOSTS[provider],
        applied_jobs_file=applied_jobs_file,
        sender_blocklist_file=sender_blocklist_file,
    )
