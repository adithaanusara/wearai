"""Admin operations. Each write records an audit entry in the same transaction."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Order, Product, User
from app.models.order import ORDER_STATUSES
from app.services import audit, auth

ROLES = ("customer", "staff", "admin")


class AdminError(Exception):
    """Something an admin asked for that is not allowed. The message is safe to show them."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _like(text: str) -> str:
    """Escapes % and _ so a search for them matches only themselves."""
    return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def list_users(
    db: Session, *, search: str | None, role: str | None, page: int, page_size: int
) -> tuple[list[User], int]:
    conditions = []
    if search:
        pattern = _like(search.strip())
        conditions.append(
            User.email.ilike(pattern, escape="\\") | User.name.ilike(pattern, escape="\\")
        )
    if role:
        conditions.append(User.role == role)

    total = db.scalar(select(func.count()).select_from(User).where(*conditions)) or 0
    users = db.scalars(
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(users), total


def change_role(db: Session, *, actor: User, user_id: int, new_role: str) -> User:
    """Changes someone's role, with the guard rails that keep the store from locking itself out."""
    if new_role not in ROLES:
        raise AdminError(422, "Unknown role.")
    if user_id == actor.id:
        raise AdminError(409, "You cannot change your own role.")

    # Lock every admin and the target, so two admins acting at once cannot leave zero admins.
    admins = list(db.scalars(select(User).where(User.role == "admin").with_for_update()))
    target = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if target is None:
        raise AdminError(404, "User not found.")
    if target.role == new_role:
        raise AdminError(409, "This user already has that role.")
    if target.role == "admin" and len(admins) <= 1:
        raise AdminError(409, "There must always be at least one admin.")

    previous = target.role
    target.role = new_role
    # Sign them out everywhere: they sign in again and carry their new role from the start.
    auth.end_all_sessions(db, target.id)
    audit.record(
        db,
        actor=actor,
        action="user.role_changed",
        entity="user",
        entity_id=target.id,
        details={"email": target.email, "from": previous, "to": new_role},
    )
    db.commit()
    return target


def list_audit(
    db: Session, *, entity: str | None, page: int, page_size: int
) -> tuple[list[AuditLog], int]:
    conditions = [AuditLog.entity == entity] if entity else []
    total = db.scalar(select(func.count()).select_from(AuditLog).where(*conditions)) or 0
    entries = db.scalars(
        select(AuditLog)
        .where(*conditions)
        .order_by(AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(entries), total


def dashboard(db: Session) -> dict:
    by_status = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    return {
        "orders_by_status": {status: by_status.get(status, 0) for status in ORDER_STATUSES},
        "products": db.scalar(select(func.count()).select_from(Product)) or 0,
        "customers": db.scalar(
            select(func.count()).select_from(User).where(User.role == "customer")
        )
        or 0,
    }
