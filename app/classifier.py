from dataclasses import dataclass
from app.applied_jobs import company_matches

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

# Senders that should never be classified as job responses, even if body keywords
# match. LinkedIn invitation emails show the invitee's job title in the body,
# which causes "recruiter" / "talent acquisition" to fire spuriously.
SENDER_BLOCKLIST = [
    "invitations@linkedin.com",
    "jobalerts-noreply@linkedin.com",
    "newsletters-noreply@linkedin.com",
    "jobs-noreply@linkedin.com",
]


@dataclass(frozen=True)
class ClassificationResult:
    matched: bool
    reason: str


def classify(
    sender: str,
    subject: str,
    body: str,
    applied_companies: list[str] | None = None,
) -> ClassificationResult:
    text = f"{subject} {body}".lower()
    sender_lower = sender.lower()

    # Blocklist check — always skip known non-job senders before anything else.
    if any(blocked in sender_lower for blocked in SENDER_BLOCKLIST):
        return ClassificationResult(matched=False, reason="sender is on the blocklist")

    # Applied-company check runs first — any email from a known application is flagged.
    if applied_companies:
        for company in applied_companies:
            if company_matches(company, sender_lower, subject):
                return ClassificationResult(
                    matched=True,
                    reason=f"applied company match: '{company}'",
                )

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
