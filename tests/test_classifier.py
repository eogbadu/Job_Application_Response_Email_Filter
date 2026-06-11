import pytest
from app.classifier import classify


def test_rejection_email_is_matched():
    result = classify(
        sender="no-reply@company.com",
        subject="Your Application Status",
        body="Unfortunately, we have decided to move forward with other candidates. We appreciate your application.",
    )
    assert result.matched is True
    assert result.reason


def test_interview_email_is_matched():
    result = classify(
        sender="hiring@company.com",
        subject="Interview Invitation",
        body="We would like to schedule an interview for the position. Please let us know your next steps.",
    )
    assert result.matched is True
    assert result.reason


def test_generic_newsletter_is_skipped():
    result = classify(
        sender="newsletter@deals.com",
        subject="This Week's Top Deals!",
        body="Check out the best sales and promotions this week. Unsubscribe at any time.",
    )
    assert result.matched is False
    assert "no matching" in result.reason


def test_sender_keyword_plus_one_body_keyword_is_matched():
    result = classify(
        sender="recruiting@acme.com",
        subject="Update from Acme",
        body="We'd like to schedule an interview with you for this opportunity.",
    )
    assert result.matched is True
    assert "recruiting" in result.reason or "interview" in result.reason


def test_one_weak_keyword_without_sender_keyword_is_skipped():
    result = classify(
        sender="info@randomstore.com",
        subject="Congratulations on your purchase!",
        body="Thank you for your recent order. Your package is on its way.",
    )
    assert result.matched is False
    # 'congratulations' alone with no job sender should not match


def test_two_body_keywords_match_without_sender_keyword():
    result = classify(
        sender="info@somecompany.com",
        subject="Your Application",
        body="We received your application and a recruiter will be in touch soon.",
    )
    assert result.matched is True


def test_applied_company_match_overrides_keyword_threshold():
    # Only 1 body keyword hit — would normally be skipped — but company is in applied list
    result = classify(
        sender="hiring@anduril.com",
        subject="Update on your application",
        body="We wanted to follow up with you.",
        applied_companies=["Anduril Industries"],
    )
    assert result.matched is True
    assert "anduril" in result.reason.lower()


def test_applied_company_no_match_when_company_absent():
    result = classify(
        sender="newsletter@randomco.com",
        subject="Weekly digest",
        body="Here are your weekly updates.",
        applied_companies=["Anduril Industries", "Google"],
    )
    assert result.matched is False


def test_applied_company_partial_word_match():
    # "Stripe" appears inside the sender domain
    result = classify(
        sender="jobs@stripe.com",
        subject="Thank you",
        body="We appreciate your interest.",
        applied_companies=["Stripe"],
    )
    assert result.matched is True
    assert "stripe" in result.reason.lower()


def test_linkedin_invitation_with_recruiter_bio_is_blocked():
    # LinkedIn invitations show the invitee's job title in the body, which can
    # contain "recruiter" or "talent acquisition" — should always be skipped.
    result = classify(
        sender="LinkedIn <invitations@linkedin.com>",
        subject="See Mindy's and other people's connections, experience, and more",
        body="Mindy works as a Talent Acquisition Specialist and recruiter at Acme Corp.",
    )
    assert result.matched is False
    assert "blocklist" in result.reason


def test_ats_sender_no_body_keywords_skipped():
    result = classify(
        sender="noreply@greenhouse.io",
        subject="Check out our blog!",
        body="Read our latest articles about company culture and team events.",
    )
    assert result.matched is False
    assert "no body keywords" in result.reason or "no matching" in result.reason
