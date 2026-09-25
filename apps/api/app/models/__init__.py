# Importing the models here registers them on Base.metadata, which Alembic reads.
from app.models.product import Product, ProductDetail, ProductImage, ProductSize, Review
from app.models.user import User

__all__ = ["Product", "ProductDetail", "ProductImage", "ProductSize", "Review", "User"]
