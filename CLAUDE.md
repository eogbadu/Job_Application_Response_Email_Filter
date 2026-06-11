# Job Email Sorter — Claude Build Spec

## Project Goal

Build a local Python v1 tool that connects to Gmail or Yahoo Mail through IMAP, scans new/unread emails, detects job-application responses using rule-based matching, and moves matching messages into a target folder/mailbox.

This is v1. Do **not** use OpenAI, Anthropic, or any LLM classifier yet. Keep it simple, local, and safe. But design the classifier interface so AI can be added later without rewriting the app.

## Core Behavior

The tool should:

1. Load configuration from `.env`.
2. Support both Gmail and Yahoo through IMAP.
3. Connect securely using IMAP over SSL.
4. Search the inbox for unread emails.
5. Parse each message's sender, subject, and plain-text body.
6. Classify messages as likely job-application responses using keyword/rule matching.
7. Create the configured target folder/mailbox if it does not exist.
8. Move matching emails into the configured target folder when `DRY_RUN=false`.
9. Only print intended actions when `DRY_RUN=true`.
10. Track processed message UIDs locally so emails are not repeatedly processed.
11. Avoid logging secrets.
12. Include clear README instructions.

## Supported Providers

Use the following IMAP hosts:

```text
Gmail: imap.gmail.com
Yahoo: imap.mail.yahoo.com
```

The app should support:

```env
EMAIL_PROVIDER=gmail
EMAIL_PROVIDER=yahoo
```

## Environment Variables

Create `.env.example` with:

```env
EMAIL_PROVIDER=yahoo
EMAIL_ADDRESS=your_email@yahoo.com
EMAIL_APP_PASSWORD=your_app_password
TARGET_FOLDER=Job Applications/Responses
DRY_RUN=true
MAX_MESSAGES=50
```

Rules:

- Never hard-code real credentials.
- Never commit `.env`.
- Include `.env` in `.gitignore`.
- Default `DRY_RUN` should be true.

## Project Structure

Create this structure:

```text
job-email-sorter/
  app/
    __init__.py
    main.py
    config.py
    classifier.py
    imap_client.py
    storage.py
  tests/
    __init__.py
    test_classifier.py
  .env.example
  .gitignore
  requirements.txt
  README.md
```

## Dependencies

Use minimal dependencies.

`requirements.txt`:

```txt
python-dotenv
pytest
```

Use Python standard library for IMAP/email parsing:

```python
imaplib
email
json
pathlib
dataclasses
```

## Classifier Requirements

Implement a rule-based classifier in `app/classifier.py`.

Suggested job-response keywords:

```python
JOB_RESPONSE_KEYWORDS = [
    "thank you for applying",
    "thanks for applying",
    "your application",
    "application received",
    "we received your application",
    "we have received your application",
    "position",
    "role",
    "job application",
    "resume",
    "recruiter",
    "talent acquisition",
    "hiring team",
    "interview",
    "next steps",
    "assessment",
    "coding challenge",
    "unfortunately",
    "not selected",
    "decided to move forward",
    "move forward with other candidates",
    "offer",
    "congratulations",
]
```

Suggested sender keywords:

```python
JOB_SENDER_KEYWORDS = [
    "greenhouse",
    "lever",
    "workday",
    "ashby",
    "smartrecruiters",
    "icims",
    "jobvite",
    "bamboohr",
    "recruiting",
    "careers",
    "talent",
    "noreply",
    "no-reply",
]
```

Classification logic:

- Return true if there are at least 2 job-response keyword hits.
- Return true if there is at least 1 sender keyword hit and at least 1 job-response keyword hit.
- Otherwise return false.

Also return a reason object or string explaining which rules matched, so dry-run output is useful.

## IMAP Requirements

Implement `ImapEmailClient` in `app/imap_client.py`.

Required methods:

```python
connect()
close()
ensure_folder_exists(folder_name: str)
select_inbox()
search_recent_messages(max_messages: int) -> list[bytes]
fetch_message(message_id: bytes) -> ParsedEmail
move_message(message_id: bytes, target_folder: str)
```

Use a typed dataclass for parsed email:

```python
@dataclass(frozen=True)
class ParsedEmail:
    uid: str
    sender: str
    subject: str
    body: str
```

For moving messages:

1. Prefer IMAP MOVE if available.
2. If MOVE fails, use copy + mark deleted + expunge.
3. Be careful to use message sequence IDs consistently. If using UIDs, use UID commands consistently.

## Storage Requirements

Implement local processed-message tracking in `app/storage.py`.

Use a local JSON file:

```text
processed_messages.json
```

Functions:

```python
load_processed_message_ids() -> set[str]
save_processed_message_ids(message_ids: set[str]) -> None
```

Add `processed_messages.json` to `.gitignore`.

## CLI / Main Program

`python -m app.main` should:

1. Load config.
2. Connect to email provider.
3. Ensure target folder exists.
4. Select inbox.
5. Search unread messages.
6. Skip already processed messages.
7. Classify each message.
8. Print `[MATCH]`, `[SKIP]`, or `[ERROR]` lines.
9. Move only if matched and `DRY_RUN=false`.
10. Save processed IDs.
11. Close connection cleanly.

Example output:

```text
Provider: yahoo
Email: user@yahoo.com
Target folder: Job Applications/Responses
Dry run: True
Found 8 unread message(s).

[MATCH] Software Engineer Application Update | careers@example.com
Reason: sender keyword 'careers', keyword 'your application'
Action: would move to Job Applications/Responses

[SKIP] Weekly Newsletter | newsletter@example.com
Reason: no matching job-response rules
```

Do not print the app password.

## Tests

Create pytest tests for the classifier.

At minimum test:

1. Rejection email is matched.
2. Interview email is matched.
3. Generic newsletter is skipped.
4. Sender keyword + one body keyword is matched.
5. One weak keyword without sender keyword is skipped.

## README Requirements

README should include:

1. What the tool does.
2. Supported providers.
3. How to create `.env`.
4. How to install dependencies.
5. How to run in dry-run mode.
6. How to switch to live mode.
7. Gmail/Yahoo app-password notes.
8. Safety warning: start with `DRY_RUN=true`.
9. Troubleshooting for authentication failures.

## Safety Constraints

- Do not ask for real credentials.
- Do not store credentials outside `.env`.
- Do not print credentials.
- Do not delete messages unless copy/move succeeds.
- Default to dry-run mode.
- Do not add AI/LLM classification in v1.
- Do not create a web app yet.
- Do not add Docker unless everything else is complete and tested.

## Definition of Done

The task is complete when:

1. Project files are created.
2. `pytest` passes.
3. `python -m app.main` runs without import errors.
4. README is clear enough for a user to set up Yahoo or Gmail.
5. `.env.example` exists.
6. `.gitignore` protects `.env` and processed-message state.
7. Dry-run mode is the default.

