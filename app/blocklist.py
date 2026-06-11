from pathlib import Path

_DEFAULT_CONTENT = """\
# Sender Blocklist
# One pattern per line — matched as a substring against the full From: address.
# Lines starting with # are comments. Blank lines are ignored.
#
# To add an entry from the command line:
#   python -m app.main --block "sender@example.com"

# LinkedIn system notifications — invitation emails embed the invitee's job
# title in the body, which causes recruiter/talent-acquisition keywords to fire.
invitations@linkedin.com
jobalerts-noreply@linkedin.com
newsletters-noreply@linkedin.com
jobs-noreply@linkedin.com

# Newsletters / false positives
hi@newsletter.doubleblindmag.com
"""


def load_sender_blocklist(filepath: str) -> list[str]:
    path = Path(filepath)
    if not path.exists():
        path.write_text(_DEFAULT_CONTENT)
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line.lower())
    return entries


def add_to_blocklist(filepath: str, sender: str) -> None:
    path = Path(filepath)
    if not path.exists():
        path.write_text(_DEFAULT_CONTENT)
    existing = load_sender_blocklist(filepath)
    if sender.lower() in existing:
        print(f"Already on blocklist: {sender}")
        return
    with path.open("a") as f:
        f.write(f"{sender}\n")
    print(f"Added to blocklist: {sender}")
