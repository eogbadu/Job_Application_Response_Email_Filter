from dataclasses import dataclass

JOB_RESPONSE_KEYWORDS = [
    "thank you for applying",
    "thanks for applying",
    "your application",
    "application received",
    "we received your application",
    "we have received your application",
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
]

# Removed: "position", "role", "offer", "congratulations" — too generic, caused
# false positives on utility bills, school emails, and marketing messages.

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
]

# Removed: "noreply", "no-reply" — appear on virtually every marketing email,
# not specific enough to signal a job-related sender.


@dataclass(frozen=True)
class ClassificationResult:
    matched: bool
    reason: str


def classify(sender: str, subject: str, body: str) -> ClassificationResult:
    text = f"{subject} {body}".lower()
    sender_lower = sender.lower()

    body_hits = [kw for kw in JOB_RESPONSE_KEYWORDS if kw in text]
    sender_hits = [kw for kw in JOB_SENDER_KEYWORDS if kw in sender_lower]

    if len(body_hits) >= 2:
        reason = f"keywords: {', '.join(repr(k) for k in body_hits[:3])}"
        return ClassificationResult(matched=True, reason=reason)

    if sender_hits and body_hits:
        reason = (
            f"sender keyword {repr(sender_hits[0])}, "
            f"keyword {repr(body_hits[0])}"
        )
        return ClassificationResult(matched=True, reason=reason)

    if body_hits:
        reason = f"only {len(body_hits)} weak keyword hit(s): {', '.join(repr(k) for k in body_hits)} — need 2+ or a matching sender"
    elif sender_hits:
        reason = f"sender keyword {repr(sender_hits[0])} but no body keywords matched"
    else:
        reason = "no matching job-response rules"

    return ClassificationResult(matched=False, reason=reason)
