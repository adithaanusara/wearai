from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app import security
from app.api.deps import TrustedOrigin, UserDep, current_user
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas import (
    LoginIn,
    RegisterIn,
    SessionOut,
    TwoFactorCodeIn,
    TwoFactorConfirmOut,
    TwoFactorDisableIn,
    TwoFactorRequiredOut,
    TwoFactorSetupOut,
    TwoFactorVerifyIn,
    UserOut,
)
from app.services import auth, login_limits, twofa

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
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        two_factor_enabled=twofa.is_enabled(user),
    )


def _sign_in(request: Request, response: Response, db: Session, user: User) -> UserOut:
    """The last step of any successful sign-in, 2FA or not: a fresh session, replacing any old
    one, and no trace of the password or code check that got here."""
    _end_current_session(request, db)
    _set_session_cookie(response, auth.start_session(db, user))
    response.headers["Cache-Control"] = "no-store"
    return _user_out(user)


def _invalid_code() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid code")


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
    return _sign_in(request, response, db, user)


@router.post("/login", response_model=UserOut | TwoFactorRequiredOut, dependencies=[TrustedOrigin])
def login(
    body: LoginIn, request: Request, response: Response, db: DbDep
) -> UserOut | TwoFactorRequiredOut:
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

    if twofa.is_enabled(user):
        # The password was right, but no session starts yet: that only happens once the code is
        # checked too, at /auth/2fa/verify. Nothing else here (the old session, the cookie) changes.
        response.headers["Cache-Control"] = "no-store"
        return TwoFactorRequiredOut(pending_token=twofa.start_pending_login(db, user))

    return _sign_in(request, response, db, user)


@router.post("/2fa/verify", response_model=UserOut, dependencies=[TrustedOrigin])
def verify_two_factor(
    body: TwoFactorVerifyIn, request: Request, response: Response, db: DbDep
) -> UserOut:
    """The second step: a code (or a recovery code) for the account a pending login belongs to."""
    user = twofa.user_for_pending_login(db, body.pending_token)
    if user is None:
        raise HTTPException(
            status_code=401, detail="This sign-in has expired. Please sign in again."
        )

    try:
        login_limits.check_twofa_allowed(db, email=user.email)
    except login_limits.TooManyAttemptsError as error:
        raise _too_many_attempts(error) from error

    secret = twofa.decrypt_secret(user.totp_secret_encrypted or "")
    ok = (
        secret is not None and twofa.verify_totp(secret, body.code)
    ) or twofa.consume_recovery_code(db, user, body.code)
    login_limits.record_attempt(
        db, kind="2fa", email=user.email, ip=login_limits.ip_hash(request), succeeded=ok
    )
    if not ok:
        raise _invalid_code()

    twofa.end_pending_login(db, body.pending_token)
    return _sign_in(request, response, db, user)


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


@router.post("/2fa/setup", response_model=TwoFactorSetupOut, dependencies=[TrustedOrigin])
def setup_two_factor(user: UserDep, db: DbDep) -> TwoFactorSetupOut:
    """Starts (or restarts) setup. Nothing is enabled yet: that needs /2fa/confirm with a real
    code, so a secret nobody actually captured can never lock an account out."""
    if not twofa.is_configured():
        raise HTTPException(
            status_code=503, detail="Two-factor authentication is not available right now."
        )
    if twofa.is_enabled(user):
        raise HTTPException(status_code=409, detail="Two-factor authentication is already on.")

    secret = twofa.generate_secret()
    user.totp_secret_encrypted = twofa.encrypt_secret(secret)
    db.commit()
    return TwoFactorSetupOut(
        secret=secret, provisioning_uri=twofa.provisioning_uri(secret, user.email)
    )


@router.post("/2fa/confirm", response_model=TwoFactorConfirmOut, dependencies=[TrustedOrigin])
def confirm_two_factor(
    body: TwoFactorCodeIn, request: Request, user: UserDep, db: DbDep
) -> TwoFactorConfirmOut:
    """Turns 2FA on, once the code proves the secret from /2fa/setup actually reached an app."""
    if twofa.is_enabled(user):
        raise HTTPException(status_code=409, detail="Two-factor authentication is already on.")
    secret = twofa.decrypt_secret(user.totp_secret_encrypted or "")
    if secret is None:
        raise HTTPException(status_code=409, detail="Set up two-factor authentication first.")

    try:
        login_limits.check_twofa_allowed(db, email=user.email)
    except login_limits.TooManyAttemptsError as error:
        raise _too_many_attempts(error) from error

    ok = twofa.verify_totp(secret, body.code)
    login_limits.record_attempt(
        db, kind="2fa", email=user.email, ip=login_limits.ip_hash(request), succeeded=ok
    )
    if not ok:
        raise _invalid_code()

    user.totp_confirmed_at = datetime.now(UTC)
    codes = twofa.generate_recovery_codes(db, user)
    db.commit()
    return TwoFactorConfirmOut(recovery_codes=codes)


@router.post("/2fa/disable", status_code=204, dependencies=[TrustedOrigin])
def disable_two_factor(
    body: TwoFactorDisableIn, request: Request, user: UserDep, db: DbDep
) -> None:
    """Turns 2FA off. Needs the password again, not just a signed-in session, so a stolen,
    already-open browser tab cannot casually turn off someone else's protection."""
    if not twofa.is_enabled(user):
        raise HTTPException(status_code=409, detail="Two-factor authentication is not on.")
    if not security.verify_password(user.password_hash, body.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    try:
        login_limits.check_twofa_allowed(db, email=user.email)
    except login_limits.TooManyAttemptsError as error:
        raise _too_many_attempts(error) from error

    secret = twofa.decrypt_secret(user.totp_secret_encrypted or "")
    ok = (
        secret is not None and twofa.verify_totp(secret, body.code)
    ) or twofa.consume_recovery_code(db, user, body.code)
    login_limits.record_attempt(
        db, kind="2fa", email=user.email, ip=login_limits.ip_hash(request), succeeded=ok
    )
    if not ok:
        raise _invalid_code()

    # Not `end_all_sessions`: reaching this point already needed the password and a valid code,
    # so there is nothing left to protect against by signing the caller out of their own session.
    twofa.disable(db, user)
    db.commit()
