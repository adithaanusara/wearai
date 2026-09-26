import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import TrustedOrigin, current_user
from app.config import settings
from app.db import get_db
from app.models import User
from app.schemas_chat import ChatIn, ChatOut, ReplyOut
from app.services import chat_limits
from app.services.chat import ChatUnavailableError, ModelGateway, Turn, get_gateway, run_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _unavailable() -> HTTPException:
    # The same answer whether the assistant is switched off, has no key, or the provider failed.
    return HTTPException(
        status_code=503,
        detail={
            "code": "chat_unavailable",
            "message": "The assistant is not available right now. Please try again later.",
        },
    )


@router.post("", response_model=ChatOut, dependencies=[TrustedOrigin])
def chat(
    body: ChatIn,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(current_user)],
    gateway: Annotated[ModelGateway | None, Depends(get_gateway)],
) -> ChatOut:
    """Answers a shopper's question using the store's own data. The provider key stays here."""
    if gateway is None or not settings.chat_enabled:
        raise _unavailable()

    try:
        usage = chat_limits.start(db, chat_limits.client_key(request, user), user)
    except chat_limits.RateLimitedError as error:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "rate_limited",
                "message": "You are sending messages too quickly. Please wait a little.",
                "retryAfter": error.retry_after,
            },
            headers={"Retry-After": str(error.retry_after)},
        ) from error
    except chat_limits.DailyCapError as error:
        logger.warning("chat daily token cap reached")
        raise _unavailable() from error

    try:
        result = run_chat(gateway, db, [Turn(turn.role, turn.text) for turn in body.messages])
    except ChatUnavailableError as error:
        chat_limits.finish(db, usage, chat_limits.Outcome("error"))
        raise _unavailable() from error

    chat_limits.finish(
        db,
        usage,
        chat_limits.Outcome(
            outcome=result.outcome,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            tool_rounds=result.tool_rounds,
            provider_request_id=result.provider_request_id,
        ),
    )
    # Only counts are logged, never what was asked or answered.
    logger.info(
        "chat outcome=%s in=%s out=%s rounds=%s",
        result.outcome,
        result.input_tokens,
        result.output_tokens,
        result.tool_rounds,
    )
    response.headers["Cache-Control"] = "no-store"
    return ChatOut(reply=ReplyOut(text=result.text, product_ids=result.product_ids))
