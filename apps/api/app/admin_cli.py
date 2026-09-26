"""Command-line way to create the first admin or change a role.

There is deliberately no web page or API route that can make the first admin: whoever can run this
already controls the server and the database. Every change is written to the audit log.

    python -m app.admin_cli create-admin you@example.com --name "Your Name"
    python -m app.admin_cli set-role someone@example.com staff
"""

import argparse
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import security
from app.db import SessionLocal
from app.models import User
from app.services import audit, auth

ROLES = ("customer", "staff", "admin")


def create_admin(db: Session, *, email: str, name: str, password: str) -> User:
    """Makes the account if it does not exist, and makes it an admin either way."""
    email = email.strip().lower()
    problem = security.password_problem(password)
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        if problem:
            raise ValueError(problem)
        user = auth.register_user(db, name=name, email=email, password=password)
    previous = user.role
    user.role = "admin"
    audit.record(
        db,
        actor=None,
        action="user.role_changed",
        entity="user",
        entity_id=user.id,
        details={"email": user.email, "from": previous, "to": "admin"},
        system_label="command line",
    )
    auth.end_all_sessions(db, user.id)
    db.commit()
    return user


def set_role(db: Session, *, email: str, role: str) -> User:
    """Changes a role from the server. Unlike the API, this may change the last admin's role."""
    if role not in ROLES:
        raise ValueError("Unknown role.")
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise ValueError("No user has that email.")
    previous = user.role
    user.role = role
    audit.record(
        db,
        actor=None,
        action="user.role_changed",
        entity="user",
        entity_id=user.id,
        details={"email": user.email, "from": previous, "to": role},
        system_label="command line",
    )
    auth.end_all_sessions(db, user.id)
    db.commit()
    return user


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.admin_cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-admin", help="create an admin, or promote an account")
    create.add_argument("email")
    create.add_argument("--name", default="Admin")

    change = commands.add_parser("set-role", help="set an account's role")
    change.add_argument("email")
    change.add_argument("role", choices=ROLES)

    args = parser.parse_args(argv)
    try:
        with SessionLocal() as db:
            if args.command == "create-admin":
                exists = db.scalar(select(User.id).where(User.email == args.email.strip().lower()))
                password = "" if exists else getpass.getpass("Password (not shown): ")
                user = create_admin(db, email=args.email, name=args.name, password=password)
            else:
                user = set_role(db, email=args.email, role=args.role)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"{user.email} is now {user.role}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
