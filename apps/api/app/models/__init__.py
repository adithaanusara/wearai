# Importing the models here registers them on Base.metadata, which Alembic reads.
from app.models.audit_log import AuditLog
from app.models.chat_usage import ChatUsage
from app.models.order import Order, OrderItem, OrderStatusHistory, PaymentEvent
from app.models.product import Product, ProductDetail, ProductImage, ProductSize, Review
from app.models.session import UserSession
from app.models.user import User

__all__ = [
    "AuditLog",
    "ChatUsage",
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "PaymentEvent",
    "Product",
    "ProductDetail",
    "ProductImage",
    "ProductSize",
    "Review",
    "User",
    "UserSession",
]
