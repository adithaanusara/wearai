from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import admin_cli
from app.config import settings
from app.models import AuditLog, User
from app.services import twofa

TEST_KEY = "MzRuJGsBgC9T4CXs2hN9fwVK8LrMOahRjY_Useparjs="


def test_create_admin_makes_a_new_account_an_admin(db: Session) -> None:
    user = admin_cli.create_admin(
        db, email="Owner@Example.com", name="Owner", password="sunrise2026"
    )

    assert user.email == "owner@example.com"
    assert user.role == "admin"
    entry = db.scalars(select(AuditLog)).one()
    assert entry.actor_email == "command line"
    assert entry.details == {"email": "owner@example.com", "from": "customer", "to": "admin"}


def test_create_admin_rejects_a_weak_password_for_a_new_account(db: Session) -> None:
    with pytest.raises(ValueError):
        admin_cli.create_admin(db, email="owner@example.com", name="Owner", password="short")

    assert db.scalar(select(User)) is None


def test_create_admin_promotes_an_existing_account_and_keeps_its_password(db: Session) -> None:
    first = admin_cli.create_admin(
        db, email="owner@example.com", name="Owner", password="sunrise2026"
    )
    before = first.password_hash
    admin_cli.set_role(db, email="owner@example.com", role="customer")

    again = admin_cli.create_admin(db, email="owner@example.com", name="Ignored", password="")

    assert again.role == "admin"
    assert again.password_hash == before
    assert again.name == "Owner"


def test_set_role_validates_its_input(db: Session) -> None:
    with pytest.raises(ValueError, match="Unknown role"):
        admin_cli.set_role(db, email="a@example.com", role="root")
    with pytest.raises(ValueError, match="No user"):
        admin_cli.set_role(db, email="nobody@example.com", role="staff")


def test_reset_2fa_turns_it_off(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "totp_encryption_key", TEST_KEY)
    user = admin_cli.create_admin(
        db, email="owner@example.com", name="Owner", password="sunrise2026"
    )
    user.totp_secret_encrypted = twofa.encrypt_secret(twofa.generate_secret())
    twofa.generate_recovery_codes(db, user)
    user.totp_confirmed_at = datetime.now(UTC)
    db.commit()

    result = admin_cli.reset_two_factor(db, email="owner@example.com")

    assert not twofa.is_enabled(result)
    entry = db.scalars(select(AuditLog).where(AuditLog.action == "user.twofa_reset")).one()
    assert entry.actor_email == "command line"
    assert entry.details == {"email": "owner@example.com"}


def test_reset_2fa_refuses_an_account_without_it_on(db: Session) -> None:
    admin_cli.create_admin(db, email="owner@example.com", name="Owner", password="sunrise2026")

    with pytest.raises(ValueError, match="does not have two-factor"):
        admin_cli.reset_two_factor(db, email="owner@example.com")


def test_reset_2fa_refuses_an_unknown_email(db: Session) -> None:
    with pytest.raises(ValueError, match="No user"):
        admin_cli.reset_two_factor(db, email="nobody@example.com")
