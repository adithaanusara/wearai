import pytest

from app import security


def test_hashes_are_argon2id_and_salted() -> None:
    first = security.hash_password("sunrise2026")
    second = security.hash_password("sunrise2026")

    assert first.startswith("$argon2id$")
    assert first != second  # a fresh salt each time
    assert "sunrise2026" not in first


def test_verify_accepts_the_right_password_only() -> None:
    hashed = security.hash_password("sunrise2026")

    assert security.verify_password(hashed, "sunrise2026") is True
    assert security.verify_password(hashed, "sunrise2027") is False


def test_verify_treats_a_corrupt_hash_as_a_failure_not_an_error() -> None:
    assert security.verify_password("not-a-hash", "sunrise2026") is False
    assert security.verify_password("", "sunrise2026") is False


def test_tokens_are_long_random_and_hashed_deterministically() -> None:
    first, second = security.generate_token(), security.generate_token()

    assert first != second
    assert len(first) >= 43  # 256 bits, url-safe encoded
    assert security.hash_token(first) == security.hash_token(first)
    assert security.hash_token(first) != first
    assert len(security.hash_token(first)) == 64


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("sunrise2026", None),
        ("a1" * 64, None),  # exactly 128 characters
        ("a1" * 64 + "x", "at most 128"),
        ("short1", "at least 8"),
        ("abcdefgh", "letter and one number"),
        ("12345678", "letter and one number"),
        ("", "at least 8"),
        ("éééééééé1", "letter and one number"),  # accented letters are not ASCII letters
        ("abcdefgh٣", "letter and one number"),  # an Arabic-Indic digit is not an ASCII digit
    ],
)
def test_password_rules_match_the_website(password: str, expected: str | None) -> None:
    problem = security.password_problem(password)

    if expected is None:
        assert problem is None
    else:
        assert problem is not None and expected in problem
