import json
from types import SimpleNamespace

import groq
import httpx
import pytest
from sqlalchemy.orm import Session

from app.services.chat import ChatUnavailableError, Turn, build_request, run_chat
from app.services.chat_groq import (
    GroqGateway,
    _optional_fields,
    from_groq_response,
    to_groq_request,
)
from tests.chat_fakes import text_block, tool_use


def completion(content=None, finish_reason="stop", tool_calls=None) -> SimpleNamespace:
    return SimpleNamespace(
        id="req_groq",
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=content, tool_calls=tool_calls),
            )
        ],
        usage=SimpleNamespace(prompt_tokens=200, completion_tokens=40),
    )


def groq_call(name: str, arguments: str, call_id: str = "call_1") -> SimpleNamespace:
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))


class TranslatingGateway:
    """Groq completions played back through the real translation, so run_chat sees what it would."""

    def __init__(self, *script: SimpleNamespace) -> None:
        self.script = list(script)
        self.requests: list[dict] = []

    def create(self, **params):
        self.requests.append(to_groq_request(params))
        return from_groq_response(self.script.pop(0), _optional_fields(params["tools"]))


def test_the_request_becomes_an_openai_style_chat_with_function_tools() -> None:
    params = build_request(
        [
            {"role": "user", "content": "black hoodie?"},
            {
                "role": "assistant",
                "content": [text_block("Looking."), tool_use("search_products", {"query": "x"})],
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "[]"}],
            },
        ]
    )

    request = to_groq_request(params)

    assert request["messages"][0]["role"] == "system"
    assert "Call answer" in request["messages"][0]["content"]
    assert request["tool_choice"] == "required"
    assert request["messages"][1] == {"role": "user", "content": "black hoodie?"}
    assistant = request["messages"][2]
    assert assistant["content"] == "Looking."
    assert assistant["tool_calls"][0]["function"] == {
        "name": "search_products",
        "arguments": json.dumps({"query": "x"}),
    }
    assert request["messages"][3] == {"role": "tool", "tool_call_id": "toolu_1", "content": "[]"}
    assert {tool["function"]["name"] for tool in request["tools"]} == {
        "search_products",
        "get_product",
        "get_store_info",
        "answer",
    }
    assert not {"thinking", "output_config", "fallbacks", "betas", "system"} & request.keys()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"text": "Hi", "product_ids": ["a"]}', {"text": "Hi", "product_ids": ["a"]}),
        ('```json\n{"text": "Hi", "product_ids": []}\n```', {"text": "Hi", "product_ids": []}),
        ("Just plain words.", {"text": "Just plain words.", "product_ids": []}),
    ],
)
def test_the_final_answer_is_always_the_expected_json(raw: str, expected: dict) -> None:
    response = from_groq_response(completion(raw))

    assert response.stop_reason == "end_turn"
    assert json.loads(response.content[0].text) == expected
    assert (response.usage.input_tokens, response.usage.output_tokens) == (200, 40)


@pytest.mark.usefixtures("catalogue")
def test_a_groq_conversation_searches_then_answers(db: Session) -> None:
    gateway = TranslatingGateway(
        completion(
            finish_reason="tool_calls",
            tool_calls=[groq_call("search_products", '{"query": "hoodie", "gender": "men"}')],
        ),
        completion(
            finish_reason="tool_calls",
            tool_calls=[
                groq_call(
                    "answer",
                    '{"text": "Try the Pullover Hoodie.", "product_ids": ["m-hood-02", "nope"]}',
                    "call_2",
                )
            ],
        ),
    )

    result = run_chat(gateway, db, [Turn("user", "Do you have a black hoodie?")])

    assert (result.outcome, result.text) == ("ok", "Try the Pullover Hoodie.")
    assert result.product_ids == ["m-hood-02"]
    assert result.tool_rounds == 1
    tool_message = gateway.requests[1]["messages"][-1]
    assert tool_message["role"] == "tool" and tool_message["tool_call_id"] == "call_1"


def test_the_answer_tool_ends_the_turn_even_alongside_another_call() -> None:
    response = from_groq_response(
        completion(
            finish_reason="tool_calls",
            tool_calls=[
                groq_call("get_product", '{"product": "x"}'),
                groq_call("answer", '{"text": "Done.", "product_ids": []}', "call_2"),
            ],
        )
    )

    assert response.stop_reason == "end_turn"
    assert [block.type for block in response.content] == ["text"]
    assert json.loads(response.content[0].text) == {"text": "Done.", "product_ids": []}


def test_a_truncated_answer_is_reported_as_such() -> None:
    assert from_groq_response(completion("cut off", finish_reason="length")).stop_reason == (
        "max_tokens"
    )


def test_optional_tool_fields_accept_empty_values_that_groq_would_otherwise_reject() -> None:
    request = to_groq_request(build_request([{"role": "user", "content": "recommend something"}]))
    schemas = {
        tool["function"]["name"]: tool["function"]["parameters"] for tool in request["tools"]
    }

    search = schemas["search_products"]["properties"]
    assert search["max_price"]["type"] == ["integer", "null"]
    assert {"", None} <= set(search["gender"]["enum"])
    assert {"", None} <= set(search["category"]["enum"])
    # Required fields keep their strict schema.
    assert schemas["get_product"]["properties"]["product"] == {
        "type": "string",
        "description": "Product id or slug.",
    }
    assert None not in schemas["get_store_info"]["properties"]["topic"]["enum"]


@pytest.mark.usefixtures("catalogue")
def test_empty_optional_fields_are_dropped_before_the_tool_runs(db: Session) -> None:
    browse = (
        '{"query": "", "gender": "", "category": "", "max_price": null,'
        ' "on_sale": false, "new_only": false}'
    )
    gateway = TranslatingGateway(
        completion(finish_reason="tool_calls", tool_calls=[groq_call("search_products", browse)]),
        completion(
            finish_reason="tool_calls",
            tool_calls=[groq_call("answer", '{"text": "Here you go.", "product_ids": []}', "c2")],
        ),
    )

    result = run_chat(gateway, db, [Turn("user", "Can you recommend some clothing products?")])

    assert result.outcome == "ok"
    tool_result = gateway.requests[1]["messages"][-1]["content"]
    assert "invalid" not in tool_result.lower() and "error" not in tool_result.lower()
    assert json.loads(tool_result)  # a real product list, not a validation error


def groq_error(
    code: str, status: int = 400, failed_generation: str | None = None
) -> groq.APIStatusError:
    response = httpx.Response(status, request=httpx.Request("POST", "https://api.groq.com"))
    error_class = groq.BadRequestError if status == 400 else groq.RateLimitError
    body: dict = {"code": code}
    if failed_generation is not None:
        body["failed_generation"] = failed_generation
    return error_class("rejected", response=response, body={"error": body})


class ScriptedClient:
    """Stands in for groq.Groq: each create() raises or returns the next scripted item."""

    def __init__(self, *outcomes) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **_request):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def gateway_with(client: ScriptedClient) -> GroqGateway:
    gateway = GroqGateway("test-key")
    gateway._client = client
    return gateway


def test_a_rejected_tool_call_is_asked_again_once() -> None:
    client = ScriptedClient(
        groq_error("tool_use_failed"), completion('{"text": "Hi", "product_ids": []}')
    )

    response = gateway_with(client).create(**build_request([{"role": "user", "content": "hi"}]))

    assert client.calls == 2
    assert json.loads(response.content[0].text)["text"] == "Hi"


def test_a_second_rejected_tool_call_makes_the_assistant_unavailable() -> None:
    client = ScriptedClient(groq_error("tool_use_failed"), groq_error("tool_use_failed"))

    with pytest.raises(ChatUnavailableError):
        gateway_with(client).create(**build_request([{"role": "user", "content": "hi"}]))
    assert client.calls == 2


@pytest.mark.parametrize(
    ("code", "status"), [("invalid_api_key", 400), ("rate_limit_exceeded", 429)]
)
def test_other_provider_errors_are_not_asked_again(code: str, status: int) -> None:
    client = ScriptedClient(groq_error(code, status))

    with pytest.raises(ChatUnavailableError):
        gateway_with(client).create(**build_request([{"role": "user", "content": "hi"}]))
    assert client.calls == 1


# What Groq returned on Render for "which catogory have women section".
PROSE_ANSWER = (
    '{"name": "answer", "arguments": We have women\u2019s items in the following categories: '
    't\u2011shirts, leggings, hoodies, and shorts. \n\nproduct_ids: []"}'
)


@pytest.mark.parametrize(
    ("failed_generation", "text"),
    [
        (
            PROSE_ANSWER,
            "We have women\u2019s items in the following categories: "
            "t\u2011shirts, leggings, hoodies, and shorts.",
        ),
        (
            '{"name": "answer", "arguments": {"text": "Hi \\"there\\"", "product_ids": [}}',
            'Hi "there"',
        ),
        ('{"name": "answer", "arguments": {"product_ids": ["a"], "txt": "Hi"}}', None),
        ('{"name": "answer", "arguments": {"text": "Hi there", "product_ids": []}}', "Hi there"),
        ('{"name": "answer", "arguments": "Plain words."}', "Plain words."),
    ],
)
def test_a_rejected_answer_keeps_its_text_without_asking_again(
    failed_generation: str, text: str | None
) -> None:
    client = ScriptedClient(
        groq_error("tool_use_failed", failed_generation=failed_generation),
        completion('{"text": "Asked again", "product_ids": []}'),
    )

    response = gateway_with(client).create(**build_request([{"role": "user", "content": "hi"}]))

    expected = text if text is not None else "Asked again"
    assert json.loads(response.content[0].text) == {"text": expected, "product_ids": []}
    assert response.stop_reason == "end_turn"
    assert client.calls == (1 if text is not None else 2)


def test_a_rejected_call_to_another_tool_is_asked_again() -> None:
    client = ScriptedClient(
        groq_error(
            "tool_use_failed",
            failed_generation='{"name": "search_products", "arguments": women stuff}',
        ),
        completion('{"text": "Asked again", "product_ids": []}'),
    )

    response = gateway_with(client).create(**build_request([{"role": "user", "content": "hi"}]))

    assert client.calls == 2
    assert json.loads(response.content[0].text)["text"] == "Asked again"


@pytest.mark.usefixtures("catalogue")
def test_a_rejected_answer_reaches_the_visitor(db: Session) -> None:
    gateway = gateway_with(
        ScriptedClient(groq_error("tool_use_failed", failed_generation=PROSE_ANSWER))
    )

    result = run_chat(gateway, db, [Turn("user", "which catogory have women section")])

    assert result.outcome == "ok"
    assert result.text.startswith("We have women")
    assert "product_ids" not in result.text
    assert result.product_ids == []
