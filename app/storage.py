import json
from pathlib import Path

_STORAGE_FILE = Path("processed_messages.json")


def load_processed_message_ids() -> set[str]:
    if not _STORAGE_FILE.exists():
        return set()
    try:
        data = json.loads(_STORAGE_FILE.read_text())
        return set(data)
    except (json.JSONDecodeError, TypeError):
        return set()


def save_processed_message_ids(message_ids: set[str]) -> None:
    _STORAGE_FILE.write_text(json.dumps(sorted(message_ids), indent=2))
