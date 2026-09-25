from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Product(Base):
    """One sellable item in one colour; products sharing a style_id are colourways of one style."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("gender IN ('women', 'men', 'unisex')", name="ck_products_gender"),
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint(
            "compare_at_price IS NULL OR compare_at_price > price",
            name="ck_products_compare_at_price_above_price",
        ),
    )

    # A short readable id such as "w-tee-01"; the cart already refers to products by it.
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    style_id: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(120))
    gender: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(40), index=True)
    colour: Mapped[str] = mapped_column(String(40))
    # Money is stored as whole LKR, never as floats.
    price: Mapped[int] = mapped_column(Integer)
    compare_at_price: Mapped[int | None] = mapped_column(Integer)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    is_best_seller: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text)
    # Lower numbers come first in the default "featured" order.
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0", index=True)

    images: Mapped[list["ProductImage"]] = relationship(
        order_by="ProductImage.position", cascade="all, delete-orphan"
    )
    sizes: Mapped[list["ProductSize"]] = relationship(
        order_by="ProductSize.position", cascade="all, delete-orphan"
    )
    details: Mapped[list["ProductDetail"]] = relationship(
        order_by="ProductDetail.position", cascade="all, delete-orphan"
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(300))
    # The first image is the default; the second is shown on hover.
    position: Mapped[int] = mapped_column(SmallInteger)


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(SmallInteger)


class ProductDetail(Base):
    __tablename__ = "product_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(200))
    position: Mapped[int] = mapped_column(SmallInteger)


class Review(Base):
    """A review applies to every colour of a style, so it is keyed by style_id."""

    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    style_id: Mapped[str] = mapped_column(String(100), index=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(80))
    review_date: Mapped[date] = mapped_column(Date)
