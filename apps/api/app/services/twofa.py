"""Two-factor authentication: TOTP codes, encrypted secrets, recovery codes, and the short-lived
token that bridges a checked password to the second step.

The secret has to be encrypted, not hashed like a password, because verifying a code needs the
real value back. `TOTP_ENCRYPTION_KEY` is that encryption key, kept apart from every other secret
in this project.
"""

import secrets
import string
from datetime import UTC, datetime, timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.models import PendingLogin, RecoveryCode, User

_RECOVERY_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"


class NotConfiguredError(Exception):
    """TOTP_ENCRYPTION_KEY is not set, so 2FA cannot be set up or checked."""


class InvalidCodeError(Exception):
    """The code, or recovery code, was not right."""


def _fernet() -> Fernet:
    if not settings.totp_encryption_key:
        raise NotConfiguredError
    return Fernet(settings.totp_encryption_key.encode())


def is_configured() -> bool:
    return bool(settings.totp_encryption_key)


def is_enabled(user: User) -> bool:
    return user.totp_confirmed_at is not None


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    """The otpauth:// URI an authenticator app scans, as a QR code, to add the account."""
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.store_name)


def verify_totp(secret: str, code: str) -> bool:
    # One step (30 seconds) either side, so a slow typist or a slightly out-of-sync clock is not
    # refused for something the shopper cannot see or control.
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(encrypted: str) -> str | None:
    try:
        return _fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken:
        return None


def _new_recovery_code() -> str:
    body = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(8))
    return f"{body[:4]}-{body[4:]}"


def generate_recovery_codes(db: Session, user: User) -> list[str]:
    """Replaces any existing recovery codes with a fresh set, returned once, in the clear."""
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    codes = [_new_recovery_code() for _ in range(settings.recovery_code_count)]
    db.add_all(
        RecoveryCode(user_id=user.id, code_hash=security.hash_password(code)) for code in codes
    )
    return codes


def consume_recovery_code(db: Session, user: User, code: str) -> bool:
    """True and marks the code used, if it was one of this account's still-unused codes."""
    unused = db.scalars(
        select(RecoveryCode).where(RecoveryCode.user_id == user.id, RecoveryCode.used_at.is_(None))
    )
    for stored in unused:
        if security.verify_password(stored.code_hash, code):
            stored.used_at = datetime.now(UTC)
            return True
    return False


def start_pending_login(db: Session, user: User) -> str:
    """A short-lived token proving the password was just checked. Returns the token; only its
    hash is stored, the same way a session cookie is."""
    db.execute(delete(PendingLogin).where(PendingLogin.user_id == user.id))
    token = security.generate_token()
    db.add(
        PendingLogin(
            id=security.hash_token(token),
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.twofa_pending_login_seconds),
        )
    )
    db.commit()
    return token


def user_for_pending_login(db: Session, token: str) -> User | None:
    """The user a still-valid pending login belongs to. An expired one is removed, not reused."""
    row = db.get(PendingLogin, security.hash_token(token))
    if row is None:
        return None
    if row.expires_at <= datetime.now(UTC):
        db.delete(row)
        db.commit()
        return None
    return db.get(User, row.user_id)


def end_pending_login(db: Session, token: str) -> None:
    db.execute(delete(PendingLogin).where(PendingLogin.id == security.hash_token(token)))
    db.commit()


def disable(db: Session, user: User) -> None:
    user.totp_secret_encrypted = None
    user.totp_confirmed_at = None
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
