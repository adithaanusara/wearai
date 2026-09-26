"""Checks what the SDK really sends, by capturing the HTTP request. No network, no cost."""

import json

import anthropic
import httpx2
import pytest
from anthropic import DefaultHttpxClient

from app.config import settings
from app.services.chat import AnthropicGateway, build_request


def _gateway_that_records() -> tuple[AnthropicGateway, dict]:
    captured: dict = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.update(
            url=str(request.url), headers=dict(request.headers), body=json.loads(request.content)
        )
        return httpx2.Response(
            200,
            headers={"request-id": "req_wire"},
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "claude-opus-5",
                "content": [{"type": "text", "text": '{"text": "ok", "product_ids": []}'}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 3, "output_tokens": 4},
            },
        )

    gateway = AnthropicGateway("sk-ant-test-key")
    gateway._client = anthropic.Anthropic(
        api_key="sk-ant-test-key",
        http_client=DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
        max_retries=0,
    )
    return gateway, captured


def test_the_request_on_the_wire_has_the_intended_shape() -> None:
    gateway, captured = _gateway_that_records()

    reply = gateway.create(**build_request([{"role": "user", "content": "hi"}]))

    body = captured["body"]
    assert captured["url"] == "https://api.anthropic.com/v1/messages?beta=true"
    assert captured["headers"]["anthropic-beta"] == "server-side-fallback-2026-07-01"
    assert body["model"] == "claude-opus-5" and body["fallbacks"] == "default"
    assert body["thinking"] == {"type": "adaptive"}
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"]["schema"]["required"] == ["text", "product_ids"]
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    assert not {"temperature", "top_p", "top_k", "tool_choice", "stream"} & body.keys()
    assert reply.content[0].text == '{"text": "ok", "product_ids": []}'
    assert reply._request_id == "req_wire"


def test_the_key_goes_only_in_the_header_never_in_the_body() -> None:
    gateway, captured = _gateway_that_records()

    gateway.create(**build_request([{"role": "user", "content": "hi"}]))

    assert captured["headers"]["x-api-key"] == "sk-ant-test-key"
    assert "sk-ant-test-key" not in json.dumps(captured["body"])


def test_features_switched_off_are_absent_on_the_wire(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chat_adaptive_thinking", False)
    monkeypatch.setattr(settings, "chat_effort", "none")
    monkeypatch.setattr(settings, "chat_refusal_fallbacks", False)
    gateway, captured = _gateway_that_records()

    gateway.create(**build_request([{"role": "user", "content": "hi"}]))

    assert "anthropic-beta" not in captured["headers"]
    assert not {"thinking", "fallbacks"} & captured["body"].keys()
    assert "effort" not in captured["body"]["output_config"]
