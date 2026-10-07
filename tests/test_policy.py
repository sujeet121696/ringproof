"""The policy table (app/policy.py), row by row."""

from app.models import Contact, Profile, RiskResult
from app.policy import decide

CONTACTS = [
    Contact(id="sujeet", name="Sujeet", relation="son"),
    Contact(id="shivam", name="Shivam", relation="son"),
]
SUJEET = Profile(id="sujeet", name="Sujeet", relation="son", addresses_user_as="Maa", has_code_word=True)
SHIVAM = Profile(id="shivam", name="Shivam", relation="son", addresses_user_as="Mummy")


def kinds(score, profile=None, contact=None, org=None, alert="sujeet"):
    result = RiskResult(score=score, rationale="", claimed_contact=contact, claimed_org=org)
    return [a.kind for a in decide(result, profile, CONTACTS, alert)]


def test_low_does_nothing():
    assert kinds("low", SUJEET, "sujeet") == []


def test_medium_watches():
    assert kinds("medium", SHIVAM, "shivam") == ["watch"]


def test_high_family_with_code_word_challenges_and_alerts():
    assert kinds("high", SUJEET, "sujeet") == ["code_word_challenge", "alert_guardian"]


def test_high_family_without_code_word_checks_with_the_real_person():
    assert kinds("high", SHIVAM, "shivam") == ["is_this_you_check", "alert_guardian"]


def test_high_organisation_hangs_up_with_helpline():
    actions = decide(
        RiskResult(score="high", rationale="", claimed_org="CBI"), None, CONTACTS, "sujeet"
    )
    assert [a.kind for a in actions] == ["hang_up_helpline", "alert_guardian"]
    assert actions[0].helpline["number"] == "1930"
    assert "CBI" in actions[0].message


def test_high_unknown_caller_hangs_up():
    assert kinds("high") == ["hang_up_helpline", "alert_guardian"]


def test_high_family_claim_waits_for_profile():
    # Profile not here yet: never say "hang up" a moment before "ask the code word".
    assert kinds("high", None, "sujeet") == ["watch"]


def test_profile_of_someone_else_is_not_used():
    assert kinds("high", SHIVAM, "sujeet") == ["watch"]


def test_no_alert_contact_means_no_alert():
    assert kinds("high", SUJEET, "sujeet", alert=None) == ["code_word_challenge"]


def test_alert_names_the_guardian():
    result = RiskResult(score="high", rationale="", claimed_org="CBI")
    alert = decide(result, None, CONTACTS, "sujeet")[-1]
    assert alert.target == "sujeet" and "Sujeet" in alert.message
