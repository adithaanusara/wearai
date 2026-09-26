from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.models import User, UserSession


class EmailTakenError(Exception):
    """An account with this email already exists."""


def _now() -> datetime:
    return datetime.now(UTC)


def register_user(db: Session, *, name: str, email: str, password: str) -> User:
    user = User(name=name, email=email, password_hash=security.hash_password(password))
    try:
        # The savepoint keeps a duplicate from breaking the caller's transaction.
        with db.begin_nested():
            db.add(user)
    except IntegrityError as error:
        raise EmailTakenError from error
    return user


def authenticate(db: Session, *, email: str, password: str) -> User | None:
    """Checks a login. Unknown emails and wrong passwords look the same to the caller."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        security.verify_dummy(password)
        return None
    if not security.verify_password(user.password_hash, password):
        return None
    if security.needs_rehash(user.password_hash):
        user.password_hash = security.hash_password(password)
    return user


def start_session(db: Session, user: User) -> str:
    """Creates a session and returns the cookie token. Only the token's hash is stored."""
    now = _now()
    db.execute(
        delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at <= now)
    )
    token = security.generate_token()
    db.add(
        UserSession(
            id=security.hash_token(token),
            user_id=user.id,
            expires_at=now + timedelta(days=settings.session_days),
        )
    )
    db.commit()
    return token


def user_for_token(db: Session, token: str) -> User | None:
    """The user a valid, unexpired session belongs to. Expired sessions are removed."""
    token_hash = security.hash_token(token)
    row = db.get(UserSession, token_hash)
    if row is None:
        return None
    if row.expires_at <= _now():
        db.delete(row)
        db.commit()
        return None
    return db.get(User, row.user_id)


def end_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.id == security.hash_token(token)))
    db.commit()


def end_all_sessions(db: Session, user_id: int) -> None:
    """Signs a user out everywhere, for example after their role changes."""
    db.execute(delete(UserSession).where(UserSession.user_id == user_id))
