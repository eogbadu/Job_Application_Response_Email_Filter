import imaplib
import email
import email.header
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedEmail:
    uid: str
    sender: str
    subject: str
    body: str


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded = []
    for fragment, charset in parts:
        if isinstance(fragment, bytes):
            decoded.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(fragment)
    return "".join(decoded)


def _extract_plain_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and part.get("Content-Disposition") != "attachment":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace") if payload else ""
        return ""
    payload = msg.get_payload(decode=True)
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace") if payload else ""


class ImapEmailClient:
    def __init__(self, host: str, email_address: str, app_password: str):
        self._host = host
        self._email_address = email_address
        self._app_password = app_password
        self._conn: imaplib.IMAP4_SSL | None = None

    def connect(self) -> None:
        self._conn = imaplib.IMAP4_SSL(self._host)
        self._conn.login(self._email_address, self._app_password)

    def close(self) -> None:
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def ensure_folder_exists(self, folder_name: str) -> None:
        conn = self._require_conn()
        quoted = self._quote_folder(folder_name)
        status, _ = conn.select(quoted)
        if status != "OK":
            conn.create(quoted)

    def select_inbox(self) -> None:
        self._require_conn().select("INBOX")

    def search_recent_messages(self, max_messages: int) -> list[bytes]:
        conn = self._require_conn()
        status, data = conn.uid("SEARCH", "UNSEEN")
        if status != "OK" or not data or not data[0]:
            return []
        uids = data[0].split()
        return uids[-max_messages:]

    def fetch_message(self, message_id: bytes) -> ParsedEmail:
        conn = self._require_conn()
        status, data = conn.uid("FETCH", message_id, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            raise RuntimeError(f"Failed to fetch message UID {message_id!r}")

        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        uid = message_id.decode() if isinstance(message_id, bytes) else str(message_id)
        sender = _decode_header_value(msg.get("From", ""))
        subject = _decode_header_value(msg.get("Subject", ""))
        body = _extract_plain_text(msg)

        return ParsedEmail(uid=uid, sender=sender, subject=subject, body=body)

    def move_message(self, message_id: bytes, target_folder: str) -> None:
        conn = self._require_conn()
        quoted = self._quote_folder(target_folder)

        # Try IMAP MOVE extension first
        try:
            status, _ = conn.uid("MOVE", message_id, quoted)
            if status == "OK":
                return
        except (imaplib.IMAP4.error, AttributeError):
            pass

        # Fall back to copy + mark deleted + expunge
        status, _ = conn.uid("COPY", message_id, quoted)
        if status != "OK":
            raise RuntimeError(f"COPY to {target_folder!r} failed for UID {message_id!r}")
        conn.uid("STORE", message_id, "+FLAGS", r"(\Deleted)")
        conn.expunge()

    def _require_conn(self) -> imaplib.IMAP4_SSL:
        if self._conn is None:
            raise RuntimeError("Not connected — call connect() first")
        return self._conn

    @staticmethod
    def _quote_folder(name: str) -> str:
        # IMAP folder names with spaces must be double-quoted
        if " " in name or "/" in name:
            return f'"{name}"'
        return name
