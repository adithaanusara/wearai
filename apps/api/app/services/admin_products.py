"""Product management. Products are edited or archived, never deleted."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Product, User
from app.services import audit
from app.services.admin import AdminError, like_pattern

EDITABLE_FIELDS = ("name", "price", "compare_at_price", "description")


def list_products(
    db: Session, *, search: str | None, archived: str, page: int, page_size: int
) -> tuple[list[Product], int]:
    """`archived` is "active", "archived" or "all"."""
    conditions = []
    if archived == "active":
        conditions.append(Product.archived_at.is_(None))
    elif archived == "archived":
        conditions.append(Product.archived_at.is_not(None))
    if search and search.strip():
        pattern = like_pattern(search.strip())
        conditions.append(
            or_(
                Product.id.ilike(pattern, escape="\\"),
                Product.name.ilike(pattern, escape="\\"),
                Product.category.ilike(pattern, escape="\\"),
                Product.colour.ilike(pattern, escape="\\"),
            )
        )
    total = db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    products = db.scalars(
        select(Product)
        .options(selectinload(Product.images))
        .where(*conditions)
        .order_by(Product.position, Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(products), total


def get_product(db: Session, product_id: str) -> Product | None:
    return db.scalar(
        select(Product)
        .options(selectinload(Product.images), selectinload(Product.sizes))
        .where(Product.id == product_id)
    )


def _lock(db: Session, product_id: str, expected_updated_at: datetime) -> Product:
    """The product, locked until the end of the transaction, if it is still as the admin saw it."""
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.images), selectinload(Product.sizes))
        .where(Product.id == product_id)
        .with_for_update()
    )
    if product is None:
        raise AdminError(404, "Product not found.")
    if product.updated_at != expected_updated_at:
        raise AdminError(
            409,
            "This product was changed by someone else. Reload to see the latest version.",
            code="stale_product",
        )
    return product


def edit_product(
    db: Session, *, actor: User, product_id: str, expected_updated_at: datetime, changes: dict
) -> Product:
    """Applies the edited fields. Nothing is written when nothing actually changed."""
    product = _lock(db, product_id, expected_updated_at)

    before: dict = {}
    after: dict = {}
    for field in EDITABLE_FIELDS:
        old, new = getattr(product, field), changes[field]
        if old != new:
            before[field], after[field] = old, new
    if not after:
        db.rollback()
        return product

    for field, value in after.items():
        setattr(product, field, value)
    product.updated_at = _next_timestamp(product.updated_at)
    audit.record(
        db,
        actor=actor,
        action="product.updated",
        entity="product",
        entity_id=product.id,
        details={"name": product.name, "from": before, "to": after},
    )
    db.commit()
    return product


def set_archived(
    db: Session, *, actor: User, product_id: str, expected_updated_at: datetime, archive: bool
) -> Product:
    product = _lock(db, product_id, expected_updated_at)
    if archive == (product.archived_at is not None):
        raise AdminError(
            409,
            "This product is already archived." if archive else "This product is not archived.",
            code="already_archived" if archive else "not_archived",
        )

    product.archived_at = datetime.now(UTC) if archive else None
    product.updated_at = _next_timestamp(product.updated_at)
    audit.record(
        db,
        actor=actor,
        action="product.archived" if archive else "product.restored",
        entity="product",
        entity_id=product.id,
        details={"name": product.name},
    )
    db.commit()
    return product


def _next_timestamp(previous: datetime) -> datetime:
    """Now, but always later than the previous version, so a change never keeps the same one."""
    return max(datetime.now(UTC), previous + timedelta(microseconds=1))
