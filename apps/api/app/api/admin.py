"""The admin API. Every route needs a role, enforced here and not by the website.

Routes are grouped by the least role they need, and each group is tagged (`role:staff` or
`role:admin`) so a test can check that no route was added without protection.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.schemas import Page, UserOut
from app.schemas_admin import AdminUserOut, AuditEntryOut, DashboardOut, RoleChangeIn
from app.services import admin as admin_service

# The origin check comes first and covers every method, so a forged request from another site
# cannot change anything here.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[TrustedOrigin])
staff_routes = APIRouter(tags=["role:staff"], dependencies=[Depends(require_staff)])
admin_routes = APIRouter(tags=["role:admin"], dependencies=[Depends(require_admin)])

DbDep = Annotated[Session, Depends(get_db)]


@staff_routes.get("/me", response_model=UserOut)
def admin_me(user: StaffDep) -> UserOut:
    """Who is signed in to the admin area, and with which role."""
    return UserOut(id=user.id, name=user.name, email=user.email, role=user.role)


@staff_routes.get("/dashboard", response_model=DashboardOut)
def get_dashboard(_: StaffDep, db: DbDep) -> DashboardOut:
    return DashboardOut(**admin_service.dashboard(db))


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
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
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
