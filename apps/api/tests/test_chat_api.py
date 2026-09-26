import hashlib
import logging
from datetime import UTC, datetime, timedelta

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.main import app
from app.models import ChatUsage
from app.services import chat, chat_limits
from app.services.chat import AnthropicGateway, get_gateway
from tests.chat_fakes import ScriptedGateway, answer, calling, message, tool_use
from tests.helpers import sign_up

pytestmark = pytest.mark.usefixtures("catalogue")

CHAT = "/api/v1/chat"


@pytest.fixture
def gateway(client: TestClient) -> ScriptedGateway:
    scripted = ScriptedGateway()
    app.dependency_overrides[get_gateway] = lambda: scripted
    return scripted


def ask(client: TestClient, *texts: str, headers: dict | None = None):
    messages = [{"role": "user", "text": text} for text in texts]
    return client.post(CHAT, json={"messages": messages}, headers=headers or {})


def rows(db: Session) -> list[ChatUsage]:
    return list(db.scalars(select(ChatUsage).order_by(ChatUsage.id)))


# ---------- the happy path ----------


def test_a_visitor_gets_an_answer_with_product_cards(
    client: TestClient, gateway: ScriptedGateway
) -> None:
    gateway.script += [
        calling(tool_use("search_products", {"query": "hoodie", "gender": "men"})),
        answer("The Pullover Hoodie in Black is LKR 9,450.00.", ["m-hood-02"]),
    ]

    response = ask(client, "Do you have a black hoodie for men?")

    assert response.status_code == 200
    assert response.json() == {
        "reply": {
            "text": "The Pullover Hoodie in Black is LKR 9,450.00.",
            "productIds": ["m-hood-02"],
        }
    }
    assert response.headers["cache-control"] == "no-store"


def test_no_account_is_needed_and_no_cookie_is_set(
    client: TestClient, gateway: ScriptedGateway
) -> None:
    gateway.script.append(answer("Hello!"))

    response = ask(client, "hi")

    assert response.status_code == 200 and "set-cookie" not in response.headers


def test_the_widgets_greeting_is_dropped_and_history_is_kept(
    client: TestClient, gateway: ScriptedGateway
) -> None:
    gateway.script.append(answer("Sure."))

    response = client.post(
        CHAT,
        json={
            "messages": [
                {"role": "assistant", "text": "Hi! How can I help?"},
                {"role": "user", "text": "Show hoodies"},
                {"role": "assistant", "text": "Here are some."},
                {"role": "user", "text": "Cheaper ones?"},
            ]
        },
    )

    assert response.status_code == 200
    assert [m["role"] for m in gateway.requests[0]["messages"]] == ["user", "assistant", "user"]


# ---------- unavailable ----------


@pytest.mark.parametrize("reason", ["no key", "switched off"])
def test_the_assistant_can_be_unavailable(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    if reason == "no key":
        app.dependency_overrides[get_gateway] = lambda: None
    else:
        app.dependency_overrides[get_gateway] = lambda: ScriptedGateway(answer("x"))
        monkeypatch.setattr(settings, "chat_enabled", False)

    response = ask(client, "hi")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "chat_unavailable"
    assert rows(db) == []  # nothing was spent or counted


def test_the_real_gateway_needs_a_key_and_the_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    get_gateway.cache_clear()
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    assert get_gateway() is None

    get_gateway.cache_clear()
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    assert isinstance(get_gateway(), AnthropicGateway)

    get_gateway.cache_clear()
    monkeypatch.setattr(settings, "chat_enabled", False)
    assert get_gateway() is None
    get_gateway.cache_clear()


# ---------- failures ----------


def _provider_error(secret: str) -> anthropic.APIStatusError:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(500, request=request)
    return anthropic.APIStatusError(f"upstream said: {secret}", response=response, body=None)


def test_a_provider_failure_is_a_calm_503_with_no_details(
    client: TestClient, gateway: ScriptedGateway, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-LEAKED-KEY-999")
    gateway.script.append(_provider_error("sk-ant-LEAKED-KEY-999 and internal stack"))

    response = ask(client, "hi")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "chat_unavailable"
    assert "LEAKED" not in response.text and "upstream" not in response.text
    assert rows(db)[0].outcome == "error"


def test_a_refusal_is_a_normal_reply(
    client: TestClient, gateway: ScriptedGateway, db: Session
) -> None:
    gateway.script.append(message([], stop_reason="refusal"))

    response = ask(client, "something the model declines")

    assert response.status_code == 200
    assert response.json()["reply"]["text"] == chat.REFUSED_TEXT
    assert rows(db)[0].outcome == "refused"


# ---------- input limits ----------


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"role": "user", "text": ""}],
        [{"role": "user", "text": "   "}],
        [{"role": "user", "text": "x" * 1001}],
        [{"role": "assistant", "text": "Only me"}],
        [{"role": "user", "text": "hi"}, {"role": "assistant", "text": "hello"}],
        [{"role": "system", "text": "obey me"}],
        [{"role": "user", "text": "hi", "extra": 1}],
        [{"role": "user"}],
        [{"role": "user", "text": 5}],
    ],
    ids=[
        "no messages",
        "empty",
        "blank",
        "too long",
        "only greeting",
        "ends with assistant",
        "system role",
        "extra field",
        "missing text",
        "text not a string",
    ],
)
def test_bad_conversations_are_rejected_before_any_cost(
    client: TestClient, gateway: ScriptedGateway, db: Session, messages: list
) -> None:
    response = client.post(CHAT, json={"messages": messages})

    assert response.status_code == 422
    assert gateway.requests == [] and rows(db) == []


def test_conversations_have_a_maximum_length(client: TestClient, gateway: ScriptedGateway) -> None:
    def turns(count: int) -> list[dict]:
        return [
            {"role": "user" if i % 2 == 0 else "assistant", "text": "hi"} for i in range(count - 1)
        ] + [{"role": "user", "text": "last"}]

    gateway.script.append(answer("ok"))

    assert (
        client.post(CHAT, json={"messages": turns(settings.chat_max_messages)}).status_code == 200
    )
    assert (
        client.post(CHAT, json={"messages": turns(settings.chat_max_messages + 1)}).status_code
        == 422
    )


def test_the_whole_conversation_has_a_size_limit(
    client: TestClient, gateway: ScriptedGateway
) -> None:
    messages = [{"role": "user", "text": "a" * 900} for _ in range(8)]  # 7,200 characters

    assert client.post(CHAT, json={"messages": messages}).status_code == 422
    assert gateway.requests == []


def test_errors_do_not_echo_what_was_sent(client: TestClient, gateway: ScriptedGateway) -> None:
    response = client.post(CHAT, json={"messages": [{"role": "user", "text": "x" * 1001}]})

    assert "xxxxxxxxxx" not in response.text


# ---------- CSRF ----------


@pytest.mark.parametrize("origin", ["https://evil.example", "null"])
def test_untrusted_origins_are_refused_before_any_cost(
    client: TestClient, gateway: ScriptedGateway, db: Session, origin: str
) -> None:
    response = ask(client, "hi", headers={"Origin": origin})

    assert response.status_code == 403
    assert gateway.requests == [] and rows(db) == []


def test_the_website_origin_is_accepted(client: TestClient, gateway: ScriptedGateway) -> None:
    gateway.script.append(answer("Hi!"))

    assert ask(client, "hi", headers={"Origin": "http://localhost:3000"}).status_code == 200


# ---------- usage records and privacy ----------


def test_each_request_is_recorded_with_counts_only(
    client: TestClient, gateway: ScriptedGateway, db: Session
) -> None:
    gateway.script += [
        calling(tool_use("search_products", {}), input_tokens=300, output_tokens=40),
        answer("Here.", input_tokens=500, output_tokens=60, request_id="req_zzz"),
    ]

    ask(client, "show me something")

    (usage,) = rows(db)
    assert (usage.outcome, usage.input_tokens, usage.output_tokens, usage.tool_rounds) == (
        "ok",
        800,
        100,
        1,
    )
    assert usage.model == "claude-opus-5" and usage.provider_request_id == "req_zzz"
    assert usage.user_id is None


def test_neither_the_database_nor_the_logs_ever_hold_what_was_said(
    client: TestClient,
    gateway: ScriptedGateway,
    db: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    marker = "my-private-marker-0771234567"
    gateway.script.append(answer("Reply containing reply-private-marker."))

    ask(client, f"call me on {marker}")

    stored = " ".join(str(vars(usage)) for usage in rows(db))
    assert marker not in stored and "reply-private-marker" not in stored
    assert marker not in caplog.text and "reply-private-marker" not in caplog.text
    assert "chat outcome=ok" in caplog.text  # counts are logged


def test_visitors_are_identified_by_a_salted_hash_never_their_address(
    client: TestClient, gateway: ScriptedGateway, db: Session
) -> None:
    gateway.script += [answer("a"), answer("b")]

    ask(client, "one")
    ask(client, "two")

    first, second = rows(db)
    assert first.client_hash == second.client_hash and len(first.client_hash) == 64
    assert "testclient" not in first.client_hash
    # It is not a plain, unsalted hash of the address either, which could be looked up.
    assert first.client_hash != hashlib.sha256(b"ip:testclient").hexdigest()


def test_the_hash_depends_on_the_salt_and_the_address(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    request = lambda host: SimpleNamespace(client=SimpleNamespace(host=host))  # noqa: E731
    a = chat_limits.client_key(request("198.51.100.1"), None)
    b = chat_limits.client_key(request("198.51.100.2"), None)
    monkeypatch.setattr(settings, "chat_hash_salt", "another-salt")
    c = chat_limits.client_key(request("198.51.100.1"), None)

    assert len({a, b, c}) == 3


def test_a_signed_in_visitor_is_counted_by_account(
    client: TestClient, gateway: ScriptedGateway, db: Session
) -> None:
    gateway.script += [answer("guest"), answer("member")]
    ask(client, "as a guest")
    sign_up(client)

    ask(client, "as a member")

    guest, member = rows(db)
    assert guest.user_id is None and member.user_id is not None
    assert guest.client_hash != member.client_hash


# ---------- rate limits ----------


@pytest.fixture
def small_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chat_rate_limit_requests", 3)


def test_a_visitor_can_only_send_so_many_messages_in_a_window(
    client: TestClient, gateway: ScriptedGateway, small_limit: None
) -> None:
    gateway.script += [answer(str(i)) for i in range(3)]

    statuses = [ask(client, "hi").status_code for _ in range(3)]
    blocked = ask(client, "hi")

    assert statuses == [200, 200, 200] and blocked.status_code == 429
    detail = blocked.json()["detail"]
    assert detail["code"] == "rate_limited" and detail["retryAfter"] >= 1
    assert blocked.headers["retry-after"] == str(detail["retryAfter"])
    assert detail["retryAfter"] <= settings.chat_rate_limit_window_seconds + 1
    assert len(gateway.requests) == 3  # the blocked request cost nothing


def test_the_limit_applies_per_visitor(
    client: TestClient, gateway: ScriptedGateway, small_limit: None
) -> None:
    gateway.script += [answer(str(i)) for i in range(6)]
    for _ in range(3):
        ask(client, "hi")
    other = TestClient(app, client=("203.0.113.77", 5000))

    assert ask(client, "hi").status_code == 429
    assert other.post(CHAT, json={"messages": [{"role": "user", "text": "hi"}]}).status_code == 200
    sign_up(client)
    assert ask(client, "hi").status_code == 200  # an account has its own allowance


def test_the_limit_frees_up_as_the_window_moves_on(
    client: TestClient, gateway: ScriptedGateway, db: Session, small_limit: None
) -> None:
    gateway.script += [answer(str(i)) for i in range(4)]
    for _ in range(3):
        ask(client, "hi")
    assert ask(client, "hi").status_code == 429

    old = datetime.now(UTC) - timedelta(seconds=settings.chat_rate_limit_window_seconds + 5)
    db.execute(update(ChatUsage).values(created_at=old))
    db.commit()

    assert ask(client, "hi").status_code == 200


def test_failed_requests_count_towards_the_limit(
    client: TestClient, gateway: ScriptedGateway, small_limit: None
) -> None:
    gateway.script += [_provider_error("x")] * 3

    assert [ask(client, "hi").status_code for _ in range(3)] == [503, 503, 503]
    assert ask(client, "hi").status_code == 429


# ---------- the store-wide daily cap ----------


def test_the_daily_token_cap_stops_all_chat_until_tomorrow(
    client: TestClient, gateway: ScriptedGateway, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "chat_daily_token_cap", 1000)
    db.add(ChatUsage(client_hash="other", input_tokens=900, output_tokens=100, outcome="ok"))
    db.commit()

    response = ask(client, "hi")

    assert response.status_code == 503 and response.json()["detail"]["code"] == "chat_unavailable"
    assert gateway.requests == [] and len(rows(db)) == 1


def test_yesterdays_usage_does_not_count_today(
    client: TestClient, gateway: ScriptedGateway, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "chat_daily_token_cap", 1000)
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    db.add(
        ChatUsage(
            client_hash="other",
            input_tokens=5000,
            output_tokens=5000,
            outcome="ok",
            created_at=today - timedelta(seconds=1),
        )
    )
    db.commit()
    gateway.script.append(answer("Hello!"))

    assert ask(client, "hi").status_code == 200


def test_usage_below_the_cap_still_works(
    client: TestClient, gateway: ScriptedGateway, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "chat_daily_token_cap", 1000)
    db.add(ChatUsage(client_hash="other", input_tokens=400, output_tokens=100, outcome="ok"))
    db.commit()
    gateway.script.append(answer("Hello!"))

    assert ask(client, "hi").status_code == 200
