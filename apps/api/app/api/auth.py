from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import TrustedOrigin, UserDep, current_user
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import LoginIn, RegisterIn, SessionOut, UserOut
from app.services import auth, login_limits

router = APIRouter(prefix="/auth", tags=["auth"])

DbDep = Annotated[Session, Depends(get_db)]


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_days * 24 * 60 * 60,
        httponly=True,  # scripts cannot read it, so an XSS bug cannot steal the session
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )


def _end_current_session(request: Request, db: Session) -> None:
    """Signs out whichever session the request carried, so a new login always gets a fresh one."""
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        auth.end_session(db, token)


def _user_out(user: User) -> UserOut:
    return UserOut(id=user.id, name=user.name, email=user.email, role=user.role)


def _too_many_attempts(error: login_limits.TooManyAttemptsError) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={
            "code": "too_many_attempts",
            "message": "Too many attempts. Please try again later.",
            "retryAfter": error.retry_after,
        },
        headers={"Retry-After": str(error.retry_after)},
    )


@router.post("/register", status_code=201, response_model=UserOut, dependencies=[TrustedOrigin])
def register(body: RegisterIn, request: Request, response: Response, db: DbDep) -> UserOut:
    ip = login_limits.ip_hash(request)
    try:
        login_limits.check_register_allowed(db, ip=ip)
    except login_limits.TooManyAttemptsError as error:
        raise _too_many_attempts(error) from error

    try:
        user = auth.register_user(db, name=body.name, email=body.email, password=body.password)
    except auth.EmailTakenError as error:
        login_limits.record_attempt(db, kind="register", email=body.email, ip=ip, succeeded=False)
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from error
    login_limits.record_attempt(db, kind="register", email=body.email, ip=ip, succeeded=True)

    _end_current_session(request, db)
    _set_session_cookie(response, auth.start_session(db, user))
    response.headers["Cache-Control"] = "no-store"
    return _user_out(user)


@router.post("/login", response_model=UserOut, dependencies=[TrustedOrigin])
def login(body: LoginIn, request: Request, response: Response, db: DbDep) -> UserOut:
    ip = login_limits.ip_hash(request)
    try:
        login_limits.check_login_allowed(db, email=body.email, ip=ip)
    except login_limits.TooManyAttemptsError as error:
        raise _too_many_attempts(error) from error

    user = auth.authenticate(db, email=body.email, password=body.password)
    login_limits.record_attempt(
        db, kind="login", email=body.email, ip=ip, succeeded=user is not None
    )
    if user is None:
        # The same message whether the email is unknown or the password is wrong.
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _end_current_session(request, db)
    _set_session_cookie(response, auth.start_session(db, user))
    response.headers["Cache-Control"] = "no-store"
    return _user_out(user)


@router.post("/logout", status_code=204, dependencies=[TrustedOrigin])
def logout(request: Request, response: Response, db: DbDep) -> None:
    _end_current_session(request, db)
    _clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: UserDep, response: Response) -> UserOut:
    response.headers["Cache-Control"] = "no-store"
    return _user_out(user)


@router.get("/session", response_model=SessionOut)
def session(user: Annotated[User | None, Depends(current_user)], response: Response) -> SessionOut:
    """Like /me, but a visitor gets a 200 with no user, so the website can ask on every page."""
    response.headers["Cache-Control"] = "no-store"
    return SessionOut(user=_user_out(user) if user else None)
