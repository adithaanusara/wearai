"""Password hashing and session tokens."""

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Argon2id with the library's recommended defaults.
_hasher = PasswordHasher()

# Verified against when an email is unknown, so a missing account takes as long as a wrong password.
_DUMMY_HASH = _hasher.hash("not-a-real-password")

MIN_PASSWORD_LENGTH = 8
# Argon2 on a huge input is slow, so an upper limit keeps it from being used to tie up the server.
MAX_PASSWORD_LENGTH = 128


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def verify_dummy(password: str) -> None:
    verify_password(_DUMMY_HASH, password)


def needs_rehash(password_hash: str) -> bool:
    """True when the hash was made with older, weaker settings and should be upgraded."""
    return _hasher.check_needs_rehash(password_hash)


def generate_token() -> str:
    """A random 256-bit value for the session cookie."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only this hash is stored, so a database leak does not reveal usable session tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


def password_problem(password: str) -> str | None:
    """Returns why a password is not acceptable, or None. The rules match the website."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Use at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Use at most {MAX_PASSWORD_LENGTH} characters."
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return "Use at least one letter and one number."
    return None
