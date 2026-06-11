# Job Email Sorter

A local Python tool that connects to your Gmail or Yahoo Mail inbox via IMAP, detects job-application response emails using keyword/rule matching, and moves them into a dedicated folder.

**v1 is rule-based only — no AI or LLM required.**

---

## What it does

1. Connects to your inbox securely over IMAP SSL.
2. Scans unread messages for job-application signals — keywords in subject/body and ATS sender addresses.
3. Flags emails from companies you've applied to, even if they don't hit the keyword threshold.
4. Suppresses known false-positive senders via a blocklist.
5. Classifies each email and prints `[MATCH]`, `[SKIP]`, `[BLOCK]`, or `[ERROR]`.
6. In dry-run mode: only prints what *would* happen — no emails are moved.
7. In live mode: moves matched emails to your configured target folder.
8. Tracks processed UIDs locally so emails are never classified twice.
9. Prints a summary at the end of every run.
10. Optionally runs on a schedule with `--watch`.

---

## Supported providers

| Provider | IMAP host |
|----------|-----------|
| Gmail | `imap.gmail.com` |
| Yahoo Mail | `imap.mail.yahoo.com` |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd job-email-sorter
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```env
EMAIL_PROVIDER=yahoo          # or: gmail
EMAIL_ADDRESS=you@yahoo.com
EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
TARGET_FOLDER=Job Applications/Responses
DRY_RUN=true
MAX_MESSAGES=50
APPLIED_JOBS_FILE=applied_jobs.xlsx
SENDER_BLOCKLIST_FILE=sender_blocklist.txt
```

**Never commit `.env`.** It is already in `.gitignore`.

---

## App passwords (required)

Both Gmail and Yahoo require an **app password** — your regular account password will not work with IMAP.

### Gmail

1. Enable 2-Step Verification: <https://myaccount.google.com/security>
2. Go to **Security → App passwords**.
3. Select app: *Mail*, device: *Other*, name it `job-email-sorter`.
4. Copy the 16-character password into `EMAIL_APP_PASSWORD`.
5. Enable IMAP: Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP.

### Yahoo Mail

1. Go to **Account Security**: <https://login.yahoo.com/account/security>
2. Click **Generate app password**.
3. Select app: *Other app*, name it `job-email-sorter`.
4. Copy the password into `EMAIL_APP_PASSWORD`.
5. IMAP is enabled by default on Yahoo.

---

## Before every session

Activate the virtual environment each time you open a new terminal:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

You'll see `(.venv)` in your prompt when it's active. All `python` commands below assume the venv is active.

---

## Running in dry-run mode (safe default)

Dry run prints what the tool would do without moving any emails.

```bash
python -m app.main
```

`DRY_RUN=true` is the default. Output looks like:

```
Provider:        yahoo
Email:           you@yahoo.com
Target folder:   Job Applications/Responses
Dry run:         True
Applied jobs:    applied_jobs.xlsx (3 companies)
Sender blocklist:sender_blocklist.txt (5 entries)

Found 8 unread message(s).

[MATCH] Software Engineer Application Update | careers@example.com
Reason: sender keyword 'careers', keyword 'your application'
Action: would move to Job Applications/Responses

[SKIP] Weekly Newsletter | newsletter@example.com
Reason: no matching job-response rules

[BLOCK] See John's connections | LinkedIn <invitations@linkedin.com>

──────────────────────────────────────────────────
Summary  matched=1  skipped=6  blocked=1  errors=0  already-processed=0
──────────────────────────────────────────────────
```

---

## Switching to live mode

> **Warning:** Start with `DRY_RUN=true` and verify the output before enabling live mode. Live mode moves emails.

Edit `.env`:

```env
DRY_RUN=false
```

Then run:

```bash
python -m app.main
```

Matched emails will be moved to `TARGET_FOLDER`. The folder is created automatically if it does not exist.

---

## Watch mode (automatic scheduling)

Run the tool on a repeating schedule without setting up a cron job:

```bash
python -m app.main --watch 15   # scan every 15 minutes
```

Each cycle fetches new unread messages, skips already-processed UIDs, and prints a summary. Press **Ctrl+C** to stop.

### Run in the background (terminal can be closed)

```bash
nohup python -m app.main --watch 15 >> sorter.log 2>&1 &
```

Check the live output at any time:

```bash
tail -f sorter.log
```

### Stop a background process

Find the process ID and kill it:

```bash
pkill -f "app.main"
```

Or if you need the PID first:

```bash
pgrep -f "app.main"   # prints the PID
kill <PID>
```

### Run on a cron schedule (survives reboots)

For persistent scheduling that starts automatically after a reboot, add a cron entry instead:

```bash
crontab -e
```

```cron
*/15 * * * * cd /path/to/job-email-sorter && .venv/bin/python -m app.main >> sorter.log 2>&1
```

---

## Tracking jobs you've applied to

Open `applied_jobs.xlsx` (auto-created on first run) and add one row per application:

| Company | Job Title | Date Applied | Notes |
|---|---|---|---|
| Anduril Industries | ML Engineer | 2026-06-01 | |
| Stripe | Backend Engineer | 2026-06-05 | |

**How it works:** The company name is matched against the sender address and email subject. A match flags the email even if no job keywords are present — because any email from a company you applied to is worth reviewing. Both full-name and significant-word matching are used, so `Anduril Industries` will catch `hiring@anduril.com`.

---

## Blocking false-positive senders

`sender_blocklist.txt` is auto-created with sensible defaults (LinkedIn notification addresses, etc.). Any sender pattern in the file is skipped before keyword matching runs.

### Add from the command line

```bash
python -m app.main --block "noreply@newsletter.example.com"
```

The entry is appended to `sender_blocklist.txt` immediately.

### Edit the file directly

Open `sender_blocklist.txt` in any text editor. Each line is a substring matched against the full `From:` address. Lines starting with `#` are comments.

```text
# Block this newsletter — triggers on article body keywords
hi@newsletter.doubleblindmag.com

# Block all mail from this domain
@spammydomain.com
```

---

## Running tests

```bash
pytest
```

All 12 tests are in `tests/test_classifier.py` and exercise the classifier with no network access.

---

## Safety notes

- `.env` and `processed_messages.json` are gitignored and never committed.
- App passwords are never printed to the terminal.
- Emails are only deleted from the inbox after a successful copy to the target folder. If the copy fails, the original is preserved.
- `DRY_RUN=true` is the default — nothing moves unless you explicitly set it to `false`.

---

## Troubleshooting

### "Authentication failed" or "Login failed"

- Make sure you are using an **app password**, not your regular account password.
- Gmail: verify IMAP is enabled in Gmail settings.
- Yahoo: regenerate the app password if it stopped working.
- Check that `EMAIL_ADDRESS` matches the account you generated the password for.

### "No module named 'dotenv'"

```bash
pip install -r requirements.txt
```

### Emails are not being found

- The tool only scans **unread** messages. Mark some test emails as unread.
- Increase `MAX_MESSAGES` in `.env` if you have a large inbox.

### Target folder not being created

- Some providers require the folder path to use a different separator. Try adjusting `TARGET_FOLDER` in `.env` (e.g. use `Job_Applications` without spaces if your provider requires it).

---

## Project structure

```
job-email-sorter/
  app/
    __init__.py
    main.py          # CLI entry point (--block, --watch, summary)
    config.py        # Loads .env into typed Config
    classifier.py    # Rule-based keyword classifier
    imap_client.py   # IMAP connection, fetch, move
    storage.py       # Tracks processed UIDs in JSON
    applied_jobs.py  # Loads applied-company list from Excel
    blocklist.py     # Loads/updates sender_blocklist.txt
  tests/
    __init__.py
    test_classifier.py
  applied_jobs.xlsx      # Fill in companies you've applied to
  sender_blocklist.txt   # Senders to always skip
  .env.example
  .gitignore
  requirements.txt
  README.md
```
