"""The audit log: who did what, when. Every admin write records an entry in the same transaction."""

from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog, User

# Anything whose name contains one of these (ignoring case and underscores, so api_key and apiKey
# both match) is removed before it can reach the log.
_SECRET_WORDS = ("password", "token", "secret", "cookie", "session", "authorization", "apikey")


def scrub(value: Any) -> Any:
    """A copy of `value` without any field that could hold a secret, however deeply nested."""
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if not any(word in str(key).lower().replace("_", "") for word in _SECRET_WORDS)
        }
    if isinstance(value, list | tuple):
        return [scrub(item) for item in value]
    return value


def record(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity: str,
    entity_id: str | int,
    details: dict[str, Any] | None = None,
    system_label: str = "system",
) -> AuditLog:
    """Adds an entry to the current transaction, so the action and its record commit together."""
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else system_label,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        details=scrub(details or {}),
    )
    db.add(entry)
    return entry
