import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import admin_cli
from app.models import AuditLog, User


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
