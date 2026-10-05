import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, ProductImage

MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "alembic/versions/0012_replace_placeholder_product_photos.py"
)
UPLOAD = "/api/v1/media/0123456789abcdef0123456789abcdef.jpg"


def load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("photo_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = load_migration()


def run(db: Session, step: str) -> None:
    """Runs the migration's upgrade or downgrade inside the test's transaction, which is rolled
    back afterwards, so the shared test schema is never really migrated down."""
    db.flush()
    with Operations.context(MigrationContext.configure(db.connection())):
        getattr(migration, step)()
    db.expire_all()


def urls(db: Session, product_id: str) -> list[str]:
    return list(
        db.scalars(
            select(ProductImage.url)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.position)
        )
    )


@pytest.fixture
def seeded_before_photos(db: Session, catalogue: None) -> None:
    """The catalogue as an older seed left it: every image a placeholder, except one photo an
    admin has since uploaded in place of the cap's first placeholder."""
    for product in db.scalars(select(Product)):
        for image, placeholder in zip(product.images, migration.PLACEHOLDERS, strict=True):
            image.url = placeholder
    cap = db.get(Product, "a-cap-01")
    assert cap is not None
    cap.images[0].url = UPLOAD


@pytest.mark.usefixtures("seeded_before_photos")
def test_upgrade_swaps_placeholders_for_photos(db: Session) -> None:
    run(db, "upgrade")

    assert urls(db, "w-tee-01") == list(migration.PHOTOS["w-tee-01"])
    assert not any(url.startswith("/images/") for url in db.scalars(select(ProductImage.url)))


@pytest.mark.usefixtures("seeded_before_photos")
def test_upgrade_leaves_uploaded_photos_alone(db: Session) -> None:
    run(db, "upgrade")

    assert urls(db, "a-cap-01") == [UPLOAD, migration.PHOTOS["a-cap-01"][1]]


@pytest.mark.usefixtures("seeded_before_photos")
def test_downgrade_restores_the_placeholders(db: Session) -> None:
    run(db, "upgrade")
    run(db, "downgrade")

    assert urls(db, "w-tee-01") == list(migration.PLACEHOLDERS)
    assert urls(db, "a-cap-01") == [UPLOAD, migration.PLACEHOLDERS[1]]
