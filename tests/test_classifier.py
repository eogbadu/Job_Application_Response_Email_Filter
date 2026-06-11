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
        body="Thank you for your interest in the role at our company.",
    )
    assert result.matched is True
    # Should match: sender has 'recruiting', body has 'role'
    assert "recruiting" in result.reason or "role" in result.reason


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


def test_ats_sender_no_body_keywords_skipped():
    result = classify(
        sender="noreply@greenhouse.io",
        subject="Check out our blog!",
        body="Read our latest articles about company culture and team events.",
    )
    assert result.matched is False
    assert "no body keywords" in result.reason or "no matching" in result.reason
