"""Loads the starter catalogue into the database: `python -m app.seed`."""

import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Product, ProductDetail, ProductImage, ProductSize, Review

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogue.json"


def _build_product(data: dict) -> Product:
    return Product(
        id=data["id"],
        slug=data["slug"],
        style_id=data["style_id"],
        name=data["name"],
        gender=data["gender"],
        category=data["category"],
        colour=data["colour"],
        price=data["price"],
        compare_at_price=data["compare_at_price"],
        is_new=data["is_new"],
        is_best_seller=data["is_best_seller"],
        description=data["description"],
        images=[ProductImage(url=url, position=i) for i, url in enumerate(data["images"])],
        sizes=[ProductSize(label=label, position=i) for i, label in enumerate(data["sizes"])],
        details=[ProductDetail(text=text, position=i) for i, text in enumerate(data["details"])],
    )


def load_catalogue(session: Session, path: Path = CATALOGUE_PATH) -> tuple[int, int]:
    """Inserts or replaces the products and reviews in the file. Safe to run more than once."""
    catalogue = json.loads(path.read_text())

    for data in catalogue["products"]:
        existing = session.get(Product, data["id"])
        if existing:
            session.delete(existing)
            session.flush()
        session.add(_build_product(data))

    for data in catalogue["reviews"]:
        session.merge(
            Review(
                id=data["id"],
                style_id=data["style_id"],
                rating=data["rating"],
                title=data["title"],
                body=data["body"],
                author=data["author"],
                review_date=date.fromisoformat(data["date"]),
            )
        )

    session.commit()
    return len(catalogue["products"]), len(catalogue["reviews"])


def main() -> None:
    with SessionLocal() as session:
        products, reviews = load_catalogue(session)
    print(f"Seeded {products} products and {reviews} reviews.")


if __name__ == "__main__":
    main()
