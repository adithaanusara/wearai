"""The admin API. Every route needs a role, enforced here and not by the website.

Routes are grouped by the least role they need, and each group is tagged (`role:staff` or
`role:admin`) so a test can check that no route was added without protection.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import (
    AdminDep,
    PaginationDep,
    StaffDep,
    TrustedOrigin,
    require_admin,
    require_staff,
)
from app.db import get_db
from app.models import Order, Product
from app.schemas import Page, UserOut
from app.schemas_admin import (
    AdminImageOut,
    AdminOrderOut,
    AdminProductOut,
    AdminUserOut,
    AuditEntryOut,
    DashboardOut,
    ImageOrderIn,
    OrderSummaryOut,
    PaymentEventOut,
    ProductEditIn,
    ProductVersionIn,
    RoleChangeIn,
    StatusChangeIn,
    StatusHistoryOut,
)
from app.schemas_orders import OrderOut
from app.services import admin as admin_service
from app.services import admin_images, admin_orders, admin_products, payments
from app.services.images import MAX_BYTES
from app.storage import ImageStorage, get_storage

# The origin check comes first and covers every method, so a forged request from another site
# cannot change anything here.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[TrustedOrigin])
staff_routes = APIRouter(tags=["role:staff"], dependencies=[Depends(require_staff)])
admin_routes = APIRouter(tags=["role:admin"], dependencies=[Depends(require_admin)])

DbDep = Annotated[Session, Depends(get_db)]
StorageDep = Annotated[ImageStorage, Depends(get_storage)]


@staff_routes.get("/me", response_model=UserOut)
def admin_me(user: StaffDep) -> UserOut:
    """Who is signed in to the admin area, and with which role."""
    return UserOut(id=user.id, name=user.name, email=user.email, role=user.role)


@staff_routes.get("/dashboard", response_model=DashboardOut)
def get_dashboard(_: StaffDep, db: DbDep) -> DashboardOut:
    return DashboardOut(**admin_service.dashboard(db))


def _order_detail(db: Session, order: Order) -> AdminOrderOut:
    history = [
        StatusHistoryOut(
            from_status=h.from_status,
            to_status=h.to_status,
            actor_email=h.actor_email,
            created_at=h.created_at,
        )
        for h in admin_orders.history_for(db, order)
    ]
    payment_events = [
        PaymentEventOut(
            from_status=e.from_status,
            to_status=e.to_status,
            source=e.source,
            method=e.method,
            message=e.message,
            created_at=e.created_at,
        )
        for e in payments.events_for(db, order)
    ]
    return AdminOrderOut(
        **dict(OrderOut.from_order(order)),
        history=history,
        allowed_next=admin_orders.allowed_next(order.status),
        payment_events=payment_events,
    )


@staff_routes.get("/orders", response_model=Page[OrderSummaryOut])
def list_orders(
    _: StaffDep,
    db: DbDep,
    pagination: PaginationDep,
    status: Annotated[
        str | None, Query(pattern="^(pending|confirmed|shipped|delivered|cancelled)$")
    ] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[OrderSummaryOut]:
    orders, total = admin_orders.list_orders(
        db, status=status, search=search, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[
            OrderSummaryOut(
                reference=o.reference,
                status=o.status,
                payment_status=o.payment_status,
                email=o.email,
                full_name=o.full_name,
                total=o.total,
                created_at=o.created_at,
            )
            for o in orders
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@staff_routes.get("/orders/{reference}", response_model=AdminOrderOut)
def get_order(reference: str, _: StaffDep, db: DbDep) -> AdminOrderOut:
    order = admin_orders.get_order(db, reference)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return _order_detail(db, order)


@staff_routes.patch("/orders/{reference}/status", response_model=AdminOrderOut)
def change_order_status(
    reference: str, body: StatusChangeIn, actor: StaffDep, db: DbDep
) -> AdminOrderOut:
    try:
        order = admin_orders.change_status(
            db,
            actor=actor,
            reference=reference,
            expected_status=body.expected_status,
            new_status=body.status,
        )
    except admin_service.AdminError as error:
        db.rollback()
        raise HTTPException(status_code=error.status_code, detail=error.as_detail()) from error
    return _order_detail(db, order)


def _product_out(product: Product) -> AdminProductOut:
    return AdminProductOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        colour=product.colour,
        gender=product.gender,
        category=product.category,
        price=product.price,
        compare_at_price=product.compare_at_price,
        description=product.description,
        images=[AdminImageOut(id=image.id, url=image.url) for image in product.images],
        sizes=[size.label for size in product.sizes],
        archived=product.archived_at is not None,
        updated_at=product.updated_at,
    )


@staff_routes.get("/products", response_model=Page[AdminProductOut])
def list_products(
    _: StaffDep,
    db: DbDep,
    pagination: PaginationDep,
    search: Annotated[str | None, Query(max_length=100)] = None,
    archived: Annotated[str, Query(pattern="^(active|archived|all)$")] = "all",
) -> Page[AdminProductOut]:
    products, total = admin_products.list_products(
        db, search=search, archived=archived, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[_product_out(product) for product in products],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@staff_routes.get("/products/{product_id}", response_model=AdminProductOut)
def get_product(product_id: str, _: StaffDep, db: DbDep) -> AdminProductOut:
    product = admin_products.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return _product_out(product)


def _run_product_change(db: Session, change) -> AdminProductOut:
    try:
        product = change()
    except admin_service.AdminError as error:
        db.rollback()
        raise HTTPException(status_code=error.status_code, detail=error.as_detail()) from error
    return _product_out(product)


@admin_routes.patch("/products/{product_id}", response_model=AdminProductOut)
def edit_product(
    product_id: str, body: ProductEditIn, actor: AdminDep, db: DbDep
) -> AdminProductOut:
    return _run_product_change(
        db,
        lambda: admin_products.edit_product(
            db,
            actor=actor,
            product_id=product_id,
            expected_updated_at=body.updated_at,
            changes={
                "name": body.name,
                "price": body.price,
                "compare_at_price": body.compare_at_price,
                "description": body.description,
            },
        ),
    )


@admin_routes.post("/products/{product_id}/archive", response_model=AdminProductOut)
def archive_product(
    product_id: str, body: ProductVersionIn, actor: AdminDep, db: DbDep
) -> AdminProductOut:
    return _run_product_change(
        db,
        lambda: admin_products.set_archived(
            db,
            actor=actor,
            product_id=product_id,
            expected_updated_at=body.updated_at,
            archive=True,
        ),
    )


@admin_routes.post("/products/{product_id}/restore", response_model=AdminProductOut)
def restore_product(
    product_id: str, body: ProductVersionIn, actor: AdminDep, db: DbDep
) -> AdminProductOut:
    return _run_product_change(
        db,
        lambda: admin_products.set_archived(
            db,
            actor=actor,
            product_id=product_id,
            expected_updated_at=body.updated_at,
            archive=False,
        ),
    )


@admin_routes.post("/products/{product_id}/images", response_model=AdminProductOut, status_code=201)
def add_product_image(
    product_id: str,
    actor: AdminDep,
    db: DbDep,
    storage: StorageDep,
    updated_at: Annotated[datetime, Form(alias="updatedAt")],
    file: Annotated[UploadFile, File()],
) -> AdminProductOut:
    # One byte more than the limit is read, so an oversized file is noticed without reading it all.
    data = file.file.read(MAX_BYTES + 1)
    return _run_product_change(
        db,
        lambda: admin_images.add_image(
            db,
            storage,
            actor=actor,
            product_id=product_id,
            expected_updated_at=updated_at,
            data=data,
        ),
    )


@admin_routes.put("/products/{product_id}/images/order", response_model=AdminProductOut)
def reorder_product_images(
    product_id: str, body: ImageOrderIn, actor: AdminDep, db: DbDep
) -> AdminProductOut:
    return _run_product_change(
        db,
        lambda: admin_images.reorder_images(
            db,
            actor=actor,
            product_id=product_id,
            expected_updated_at=body.updated_at,
            image_ids=body.image_ids,
        ),
    )


@admin_routes.delete("/products/{product_id}/images/{image_id}", response_model=AdminProductOut)
def remove_product_image(
    product_id: str,
    image_id: int,
    actor: AdminDep,
    db: DbDep,
    storage: StorageDep,
    updated_at: Annotated[datetime, Query(alias="updatedAt")],
) -> AdminProductOut:
    return _run_product_change(
        db,
        lambda: admin_images.remove_image(
            db,
            storage,
            actor=actor,
            product_id=product_id,
            image_id=image_id,
            expected_updated_at=updated_at,
        ),
    )


@admin_routes.get("/users", response_model=Page[AdminUserOut])
def list_users(
    _: AdminDep,
    db: DbDep,
    pagination: PaginationDep,
    search: Annotated[str | None, Query(max_length=100)] = None,
    role: Annotated[str | None, Query(pattern="^(customer|staff|admin)$")] = None,
) -> Page[AdminUserOut]:
    users, total = admin_service.list_users(
        db, search=search, role=role, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[
            AdminUserOut(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
            )
            for user in users
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@admin_routes.patch("/users/{user_id}/role", response_model=AdminUserOut)
def change_user_role(user_id: int, body: RoleChangeIn, actor: AdminDep, db: DbDep) -> AdminUserOut:
    try:
        user = admin_service.change_role(db, actor=actor, user_id=user_id, new_role=body.role)
    except admin_service.AdminError as error:
        db.rollback()
        raise HTTPException(status_code=error.status_code, detail=error.as_detail()) from error
    return AdminUserOut(
        id=user.id, name=user.name, email=user.email, role=user.role, created_at=user.created_at
    )


@admin_routes.get("/audit-log", response_model=Page[AuditEntryOut])
def get_audit_log(
    _: AdminDep,
    db: DbDep,
    pagination: PaginationDep,
    entity: Annotated[str | None, Query(max_length=40)] = None,
) -> Page[AuditEntryOut]:
    entries, total = admin_service.list_audit(
        db, entity=entity, page=pagination.page, page_size=pagination.page_size
    )
    return Page(
        items=[
            AuditEntryOut(
                id=e.id,
                created_at=e.created_at,
                actor_email=e.actor_email,
                action=e.action,
                entity=e.entity,
                entity_id=e.entity_id,
                details=e.details,
            )
            for e in entries
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


router.include_router(staff_routes)
router.include_router(admin_routes)
