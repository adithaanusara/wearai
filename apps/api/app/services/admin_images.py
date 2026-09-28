"""Product images: add, remove and reorder. Each change follows the same rules as other product
edits: admin only, based on the version the admin saw, and recorded in the audit log."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Product, ProductImage, User
from app.services import audit, images
from app.services.admin import AdminError
from app.services.admin_products import lock_product, next_version
from app.storage import ImageStorage

MAX_IMAGES = 8


def add_image(
    db: Session,
    storage: ImageStorage,
    *,
    actor: User,
    product_id: str,
    expected_updated_at: datetime,
    data: bytes,
) -> Product:
    # The slow part (decoding) happens before the product row is locked.
    processed = images.process_upload(data)
    product = lock_product(db, product_id, expected_updated_at)
    if len(product.images) >= MAX_IMAGES:
        raise AdminError(
            409, f"A product can have at most {MAX_IMAGES} images.", code="too_many_images"
        )

    # A random name, never the uploader's, so it cannot collide or reach another folder.
    name = f"{uuid4().hex}{processed.extension}"
    storage.save(name, processed.data)
    try:
        url = storage.url_for(name)
        product.images.append(ProductImage(url=url, position=len(product.images)))
        product.updated_at = next_version(product.updated_at)
        audit.record(
            db,
            actor=actor,
            action="product.image_added",
            entity="product",
            entity_id=product.id,
            details={"name": product.name, "image": name},
        )
        db.commit()
    except BaseException:
        # Nothing was saved, so the file must not be left behind either.
        db.rollback()
        storage.delete(name)
        raise
    return product


def remove_image(
    db: Session,
    storage: ImageStorage,
    *,
    actor: User,
    product_id: str,
    image_id: int,
    expected_updated_at: datetime,
) -> Product:
    product = lock_product(db, product_id, expected_updated_at)
    image = next((item for item in product.images if item.id == image_id), None)
    if image is None:
        raise AdminError(404, "Image not found.")
    if len(product.images) == 1:
        raise AdminError(409, "A product must keep at least one image.", code="last_image")

    url = image.url
    product.images.remove(image)
    for position, item in enumerate(product.images):
        item.position = position
    product.updated_at = next_version(product.updated_at)
    audit.record(
        db,
        actor=actor,
        action="product.image_removed",
        entity="product",
        entity_id=product.id,
        details={"name": product.name, "image": url},
    )
    db.commit()

    # The file goes only after the database change is safe. If this fails, an unused file is left
    # behind, which is harmless; the reverse (a row with no file) would be a broken picture.
    name = storage.name_for(url)
    if name is not None:
        try:
            storage.delete(name)
        except Exception:  # noqa: BLE001 -- either backend's own failure is equally harmless here
            pass
    return product


def reorder_images(
    db: Session,
    *,
    actor: User,
    product_id: str,
    expected_updated_at: datetime,
    image_ids: list[int],
) -> Product:
    product = lock_product(db, product_id, expected_updated_at)
    current = [item.id for item in product.images]
    if sorted(image_ids) != sorted(current):
        raise AdminError(422, "Send each of the product's images exactly once.")
    if image_ids == current:
        db.rollback()
        return product

    by_id = {item.id: item for item in product.images}
    for position, image_id in enumerate(image_ids):
        by_id[image_id].position = position
    product.updated_at = next_version(product.updated_at)
    audit.record(
        db,
        actor=actor,
        action="product.images_reordered",
        entity="product",
        entity_id=product.id,
        details={"name": product.name, "from": current, "to": image_ids},
    )
    db.commit()
    db.refresh(product)
    return product
