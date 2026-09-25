"""The store's collections. The same slugs and rules are used by the website."""

from dataclasses import dataclass

from sqlalchemy import ColumnElement, and_, or_

from app.models import Product


@dataclass(frozen=True)
class Collection:
    slug: str
    title: str
    condition: ColumnElement[bool]


_CATEGORIES = {
    "t-shirts": "T-Shirts",
    "leggings": "Leggings",
    "hoodies": "Hoodies",
    "shorts": "Shorts",
    "joggers": "Joggers",
}
_ACCESSORIES = {"bags": "Bags", "caps": "Caps", "socks": "Socks", "bottles": "Bottles"}

_unisex = Product.gender == "unisex"


def _gender_collections(gender: str, title: str) -> list[Collection]:
    # Unisex products, such as accessories, appear in both the women's and men's collections.
    in_gender = or_(Product.gender == gender, _unisex)
    return [
        Collection(gender, title, in_gender),
        Collection(f"{gender}-new", f"{title} New Arrivals", and_(in_gender, Product.is_new)),
        Collection(
            f"{gender}-best-sellers",
            f"{title} Best Sellers",
            and_(in_gender, Product.is_best_seller),
        ),
        *(
            Collection(
                f"{gender}-{category}",
                f"{title} {label}",
                and_(in_gender, Product.category == category),
            )
            for category, label in _CATEGORIES.items()
        ),
    ]


_ALL = [
    *_gender_collections("women", "Women"),
    *_gender_collections("men", "Men"),
    Collection("accessories", "Accessories", _unisex),
    Collection("accessories-new", "Accessories New Arrivals", and_(_unisex, Product.is_new)),
    *(
        Collection(category, label, Product.category == category)
        for category, label in _ACCESSORIES.items()
    ),
    Collection("new", "New Arrivals", Product.is_new),
    Collection("last-chance", "Last Chance", Product.compare_at_price.is_not(None)),
]

COLLECTIONS: dict[str, Collection] = {collection.slug: collection for collection in _ALL}


def get_collection(slug: str) -> Collection | None:
    return COLLECTIONS.get(slug)
