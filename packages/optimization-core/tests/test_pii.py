import pytest

from optimization_core.pii import detect_pii


def categories(text: str) -> set[str]:
    return {m.category for m in detect_pii(text)}


@pytest.mark.parametrize(
    "text",
    [
        "Contact me at jane.doe@example.com for details.",
        "reach out: first.last+tag@sub.example.co.uk",
    ],
)
def test_detects_email(text: str) -> None:
    assert "email" in categories(text)


@pytest.mark.parametrize(
    "text",
    [
        "Call me at (415) 555-0132 tomorrow.",
        "My number is +1 415-555-0132.",
        "Phone: 415.555.0132",
    ],
)
def test_detects_phone_with_separators(text: str) -> None:
    assert "phone" in categories(text)


def test_does_not_flag_bare_digit_runs_as_phone() -> None:
    # Deliberate precision tradeoff (see pii.py docstring): unseparated digit runs
    # are common as order/ticket/ID numbers and must not trip the privacy gate.
    assert "phone" not in categories("Order number 4155550132 was shipped yesterday.")


def test_detects_ssn() -> None:
    assert "ssn" in categories("SSN on file: 123-45-6789.")


def test_detects_luhn_valid_credit_card() -> None:
    assert "credit_card" in categories("Card: 4111 1111 1111 1111 expires 12/29.")
    assert "credit_card" in categories("Card 4111111111111111 on file.")


def test_does_not_flag_luhn_invalid_digit_run_as_credit_card() -> None:
    assert "credit_card" not in categories("Tracking number 1234567812345678 assigned.")


# Built by concatenation rather than as literal contiguous strings so these
# obviously-fake fixtures (they satisfy the *shape* our regex looks for, nothing more)
# don't visually match real-token scanners like GitHub push protection.
_FAKE_KEY_FIXTURES = [
    "key: " + "sk-" + "abcdefghijklmnopqrstuvwx",
    "token " + "ghp_" + "ABCDEFGHIJ1234567890abcd",
    "slack " + "xoxb-" + "1234567890" + "-" + "abcdefghijklmnop",
    "aws " + "AKIA" + "ABCDEFGHIJKLMNOP",
    "google " + "AIza" + "SyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567",
]


@pytest.mark.parametrize("text", _FAKE_KEY_FIXTURES)
def test_detects_known_api_key_formats(text: str) -> None:
    assert "api_key" in categories(text)


def test_clean_prompt_has_no_matches() -> None:
    assert detect_pii("Write a short poem about autumn leaves falling.") == []


def test_scans_inside_fenced_code() -> None:
    text = "Here is my config:\n```env\nAPI_KEY=" + "sk-" + "abcdefghijklmnopqrstuvwx" + "\n```"
    assert "api_key" in categories(text)


def test_detects_multiple_categories_in_one_prompt() -> None:
    text = "Email me at a@b.com or call (415) 555-0132; card 4111 1111 1111 1111."
    found = categories(text)
    assert {"email", "phone", "credit_card"} <= found
