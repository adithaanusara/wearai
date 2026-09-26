"""Tests for the development fake AI, and, through it, the real SDK-to-endpoint path for free."""

import threading
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models import ChatUsage
from app.services import chat
from app.services.chat import AnthropicGateway, get_gateway
from devtools.fake_anthropic import MARKER, make_server, respond

pytestmark = pytest.mark.usefixtures("catalogue")


def first_step(question: str) -> dict:
    status, body = respond({"messages": [{"role": "user", "content": question}]})
    assert status == 200
    return body


def tool_call(question: str) -> tuple[str, dict]:
    block = first_step(question)["content"][0]
    assert block["type"] == "tool_use", block
    return block["name"], block["input"]


# ---------- how it decides (pure) ----------


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Do you have a black hoodie for men?",
            ("search_products", {"category": "hoodies", "gender": "men", "query": "black"}),
        ),
        ("leggings for women", ("search_products", {"category": "leggings", "gender": "women"})),
        ("anything on sale?", ("search_products", {"on_sale": True})),
        ("what is new?", ("search_products", {"new_only": True})),
        ("caps under 3,000", ("search_products", {"category": "caps", "max_price": 3000})),
        ("show me something", ("search_products", {})),
        ("How much is delivery?", ("get_store_info", {"topic": "delivery"})),
        ("can I pay cash on delivery", ("get_store_info", {"topic": "payment"})),
        ("what size should I get", ("get_store_info", {"topic": "sizing"})),
        ("I want a refund", ("get_store_info", {"topic": "returns"})),
        ("how do I contact you", ("get_store_info", {"topic": "contact"})),
    ],
)
def test_it_picks_a_tool_from_keywords(question: str, expected: tuple[str, dict]) -> None:
    assert tool_call(question) == expected


def test_policy_questions_win_over_product_words() -> None:
    assert tool_call("can I return a hoodie?") == ("get_store_info", {"topic": "returns"})


def test_small_talk_and_off_topic_need_no_tool() -> None:
    for question in ("hello!", "what is the meaning of life"):
        assert first_step(question)["stop_reason"] == "end_turn"


def test_the_server_can_wait_before_answering_like_a_real_model() -> None:
    import time

    import httpx2

    server = make_server(port=0, delay=0.3)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        started = time.monotonic()
        response = httpx2.post(
            f"http://127.0.0.1:{server.server_port}/v1/messages",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        elapsed = time.monotonic() - started
    finally:
        server.shutdown()
        server.server_close()

    assert response.status_code == 200 and elapsed >= 0.3


def test_every_answer_is_marked_as_fake() -> None:
    assert MARKER.strip() in first_step("hello")["content"][0]["text"]


def test_special_words_trigger_a_refusal_and_an_outage() -> None:
    assert first_step("REFUSE this")["stop_reason"] == "refusal"
    status, body = respond({"messages": [{"role": "user", "content": "DOWN please"}]})
    assert status == 500 and body["type"] == "error"


# ---------- through the real SDK, HTTP, tool loop and endpoint ----------


@pytest.fixture
def fake_ai(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    gateway = AnthropicGateway("dev-fake-key")
    app.dependency_overrides[get_gateway] = lambda: gateway
    yield
    server.shutdown()
    server.server_close()


def ask(client: TestClient, text: str):
    return client.post("/api/v1/chat", json={"messages": [{"role": "user", "text": text}]})


def test_delivery_answers_use_the_real_fees(client: TestClient, fake_ai: None) -> None:
    reply = ask(client, "How much is delivery?").json()["reply"]

    assert "LKR 450.00" in reply["text"] and "LKR 15,000.00" in reply["text"]
    assert "LKR 950.00" in reply["text"] and MARKER in reply["text"]
    assert reply["productIds"] == []


def test_product_answers_come_from_the_database(client: TestClient, fake_ai: None) -> None:
    reply = ask(client, "Do you have a black hoodie for men?").json()["reply"]

    assert reply["productIds"] == ["m-hood-02"]
    assert "Pullover Hoodie in Black (LKR 9,450.00)" in reply["text"]


def test_price_filters_are_applied_by_the_real_tool(client: TestClient, fake_ai: None) -> None:
    ids = ask(client, "show me something under 3000").json()["reply"]["productIds"]

    assert ids and set(ids) <= {"a-cap-01", "a-sock-01", "a-bottle-01"}


def test_a_search_with_no_match_is_answered_honestly(client: TestClient, fake_ai: None) -> None:
    reply = ask(client, "leggings under 500").json()["reply"]

    assert "couldn't find" in reply["text"] and reply["productIds"] == []


def test_refusals_and_outages_are_handled_like_the_real_thing(
    client: TestClient, fake_ai: None, db: Session
) -> None:
    refused = ask(client, "REFUSE this").json()["reply"]["text"]
    down = ask(client, "DOWN please")

    assert refused == chat.REFUSED_TEXT
    assert down.status_code == 503 and down.json()["detail"]["code"] == "chat_unavailable"
    assert [u.outcome for u in db.scalars(select(ChatUsage).order_by(ChatUsage.id))] == [
        "refused",
        "error",
    ]


def test_token_use_is_recorded_across_the_tool_round(
    client: TestClient, fake_ai: None, db: Session
) -> None:
    ask(client, "How much is delivery?")

    usage = db.scalars(select(ChatUsage)).one()
    assert (usage.input_tokens, usage.output_tokens, usage.tool_rounds) == (1600, 160, 1)
    assert usage.provider_request_id == "req_devfake"
