# Job Email Sorter

A local Python tool that connects to your Gmail or Yahoo Mail inbox via IMAP, detects job-application response emails using keyword/rule matching, and moves them into a dedicated folder.

**v1 is rule-based only — no AI or LLM required.**

---

## What it does

1. Connects to your inbox securely over IMAP SSL.
2. Scans unread messages for job-application signals (keywords in subject/body and ATS sender addresses).
3. Classifies each email and prints `[MATCH]`, `[SKIP]`, or `[ERROR]`.
4. In dry-run mode: only prints what *would* happen — no emails are moved.
5. In live mode: moves matched emails to your configured target folder.
6. Tracks processed UIDs locally so emails are never classified twice.

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

## Running in dry-run mode (safe default)

Dry run prints what the tool would do without moving any emails.

```bash
python -m app.main
```

`DRY_RUN=true` is the default. Output looks like:

```
Provider: yahoo
Email: you@yahoo.com
Target folder: Job Applications/Responses
Dry run: True
Found 8 unread message(s).

[MATCH] Software Engineer Application Update | careers@example.com
Reason: sender keyword 'careers', keyword 'your application'
Action: would move to Job Applications/Responses

[SKIP] Weekly Newsletter | newsletter@example.com
Reason: no matching job-response rules
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

## Running tests

```bash
pytest
```

All tests are in `tests/test_classifier.py` and test the rule-based classifier with no network access.

---

## Safety notes

- `.env` and `processed_messages.json` are gitignored and never committed.
- App passwords are never printed to the terminal.
- Emails are only deleted from the inbox after a successful copy to the target folder (copy → mark deleted → expunge). If the copy fails, the original is preserved.
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

- Some providers require the folder path to use a different separator. Try adjusting `TARGET_FOLDER` in `.env` (e.g., use `Job_Applications` without spaces if your provider requires it).

---

## Project structure

```
job-email-sorter/
  app/
    __init__.py
    main.py          # CLI entry point
    config.py        # Loads .env into typed Config
    classifier.py    # Rule-based keyword classifier
    imap_client.py   # IMAP connection, fetch, move
    storage.py       # Tracks processed UIDs in JSON
  tests/
    __init__.py
    test_classifier.py
  .env.example
  .gitignore
  requirements.txt
  README.md
```
