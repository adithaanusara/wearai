"""replace placeholder product photos

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-05 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The seed only adds products that are missing, so a database seeded before the catalogue had
# photos keeps its placeholders forever. This swaps them for the photos now in catalogue.json.
# The list is copied in rather than read from that file, so this migration keeps doing the same
# thing however the catalogue changes later.
PLACEHOLDERS = ("/images/placeholder.svg", "/images/placeholder-alt.svg")
_UNSPLASH = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=1200&q=80"
PHOTOS: dict[str, tuple[str, str]] = {
    product_id: (_UNSPLASH.format(first), _UNSPLASH.format(second))
    for product_id, (first, second) in {
        "w-tee-01": ("1610502778270-c5c6f4c7d575", "1759572095384-1a7e646d0d4f"),
        "w-tee-02": ("1651761179569-4ba2aa054997", "1778671394516-8270eac13c42"),
        "w-leg-01": ("1762331655528-4af4bccf7c62", "1706029831374-e236f69cbe8b"),
        "w-leg-03": ("1626026397008-3316047db4fc", "1612310480700-e64c5c42dae7"),
        "w-hood-01": ("1620799140188-3b2a02fd9a77", "1688111421205-a0a85415b224"),
        "w-short-01": ("1649345946706-afbf86eee046", "1789110519888-758d7ab3908e"),
        "w-leg-02": ("1597299001669-6454fec8ac25", "1643834068973-903e3c260269"),
        "m-tee-01": ("1521572163474-6864f9cf17ab", "1581655353564-df123a1eb820"),
        "m-short-01": ("1600878585887-c2b9530999a1", "1579758682665-53a1a614eea6"),
        "m-hood-01": ("1677538537484-324385aff147", "1556821840-3a63f95609a7"),
        "m-hood-02": ("1673092147872-5ddb03194341", "1615320876716-0fc796a5010f"),
        "m-jog-01": ("1789110854262-ec66f0648ec7", "1506629082955-511b1aa562c8"),
        "m-tee-02": ("1571455786673-9d9d6c194f90", "1654570818480-54524bf0186b"),
        "a-bag-01": ("1699319656128-6e353d6b9c7c", "1579556397147-48e5ffa85b84"),
        "a-cap-01": ("1737666636073-f15d9762cf83", "1542529727-24cb357c57d2"),
        "a-sock-01": ("1589895868481-e2ffe351cccb", "1589895868947-b51095d437f3"),
        "a-bottle-01": ("1598410924570-6e37b6c54fe6", "1624469786827-13be4e09a992"),
    }.items()
}

_SWAP = sa.text(
    "UPDATE product_images SET url = :new WHERE product_id = :product_id AND url = :old"
)


def _swap(pairs: list[tuple[str, str, str]]) -> None:
    """Only rows still holding the exact old URL change, so photos an admin uploaded stay put."""
    op.get_bind().execute(
        _SWAP, [{"product_id": pid, "old": old, "new": new} for pid, old, new in pairs]
    )


def upgrade() -> None:
    _swap(
        [
            (product_id, placeholder, photo)
            for product_id, photos in PHOTOS.items()
            for placeholder, photo in zip(PLACEHOLDERS, photos, strict=True)
        ]
    )


def downgrade() -> None:
    _swap(
        [
            (product_id, photo, placeholder)
            for product_id, photos in PHOTOS.items()
            for placeholder, photo in zip(PLACEHOLDERS, photos, strict=True)
        ]
    )
