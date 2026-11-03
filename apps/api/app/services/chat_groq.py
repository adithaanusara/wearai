"""Groq as the chat model, behind the same gateway as Anthropic.

`run_chat` speaks the Anthropic Messages shape. This gateway translates each request into Groq's
OpenAI-style chat completion and the reply back, so the conversation loop, the tools and the
safety checks around them stay the same whichever provider answers.
"""

import json
import logging
from types import SimpleNamespace
from typing import Any

import groq

from app.config import settings
from app.services.chat import ANSWER_SCHEMA, ChatUnavailableError

logger = logging.getLogger(__name__)

# Anthropic enforces the answer's shape with a JSON schema. Here the final answer is a call to this
# tool instead, and the model must call some tool every turn, so the shape holds as well.
ANSWER_TOOL = "answer"
ANSWER_INSTRUCTION = f"""

Reply format:
- Always reply by calling a tool. Call {ANSWER_TOOL} to give the customer your final answer, with \
its text and the product_ids to show (an empty list when you recommend no products)."""

_STOP_REASONS = {
    "stop": "end_turn",
    "tool_calls": "tool_use",
    "length": "max_tokens",
    "content_filter": "refusal",
}


class GroqGateway:
    def __init__(self, api_key: str) -> None:
        # One retry for transient errors; the visitor is waiting, so more would only add delay.
        self._client = groq.Groq(
            api_key=api_key, timeout=settings.chat_timeout_seconds, max_retries=1
        )

    def create(self, **params: Any) -> Any:
        request = to_groq_request(params)
        # The model's reply is sampled, so a tool call Groq rejected (code "tool_use_failed") is
        # usually fine when asked again. One more try, then the visitor sees "unavailable".
        for attempt in range(2):
            try:
                completion = self._client.chat.completions.create(**request)
                break
            except groq.APIError as error:
                status = getattr(error, "status_code", None)
                code = _error_code(error)
                if code == "tool_use_failed" and attempt == 0:
                    logger.warning("chat provider rejected a tool call; asking again")
                    continue
                # Only the kind of error is logged: no message text, nothing that could hold a key.
                log = logger.error if status in (400, 401, 403, 404) else logger.warning
                log("chat provider error: %s status=%s code=%s", type(error).__name__, status, code)
                raise ChatUnavailableError from error
        return from_groq_response(completion, _optional_fields(params["tools"]))


def _error_code(error: groq.APIError) -> str | None:
    """Groq's short error code, such as "tool_use_failed" or "rate_limit_exceeded"."""
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        inner = body.get("error", body)
        if isinstance(inner, dict) and isinstance(inner.get("code"), str):
            return inner["code"]
    return None


def _optional_fields(tools: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {
        tool["name"]: set(tool["input_schema"].get("properties", {}))
        - set(tool["input_schema"].get("required", []))
        for tool in tools
    }


def _groq_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """The schema with optional fields that also accept null or "".

    Groq checks every tool call against its schema and rejects the whole reply when a model fills
    an optional field with null or "" (as it does when asked to leave fields empty to browse).
    Those empty values are dropped again before the tool runs, so the tools see the same input.
    """
    required = set(schema.get("required", []))
    properties: dict[str, Any] = {}
    for name, prop in schema.get("properties", {}).items():
        if name not in required:
            prop = dict(prop)
            types = prop.get("type")
            if isinstance(types, str):
                prop["type"] = [types, "null"]
            if "enum" in prop:
                prop["enum"] = [*prop["enum"], "", None]
        properties[name] = prop
    return {**schema, "properties": properties}


def to_groq_request(params: dict[str, Any]) -> dict[str, Any]:
    """Anthropic-only settings (thinking, effort, fallbacks, caching) have no Groq equivalent."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": params["system"] + ANSWER_INSTRUCTION}
    ]
    for message in params["messages"]:
        messages.extend(_to_groq_messages(message))

    return {
        "model": settings.groq_model,
        "max_completion_tokens": params["max_tokens"],
        "messages": messages,
        "tools": [
            *(
                _function(tool["name"], tool["description"], _groq_schema(tool["input_schema"]))
                for tool in params["tools"]
            ),
            _function(ANSWER_TOOL, "Give the customer your final answer.", ANSWER_SCHEMA),
        ],
        "tool_choice": "required",
    }


def _function(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {"name": name, "description": description, "parameters": parameters},
    }


def _to_groq_messages(message: dict[str, Any]) -> list[dict[str, Any]]:
    content = message["content"]
    if isinstance(content, str):
        return [{"role": message["role"], "content": content}]

    if message["role"] == "user":
        # A list of tool results: Groq takes each as its own "tool" message.
        return [
            {"role": "tool", "tool_call_id": item["tool_use_id"], "content": item["content"]}
            for item in content
        ]

    text = "".join(block.text for block in content if block.type == "text")
    tool_calls = [
        {
            "id": block.id,
            "type": "function",
            "function": {"name": block.name, "arguments": json.dumps(block.input)},
        }
        for block in content
        if block.type == "tool_use"
    ]
    out: dict[str, Any] = {"role": "assistant", "content": text or None}
    if tool_calls:
        out["tool_calls"] = tool_calls
    return [out]


def from_groq_response(
    completion: Any, optional_fields: dict[str, set[str]] | None = None
) -> SimpleNamespace:
    """The completion in the shape `run_chat` reads from Anthropic.

    `optional_fields` names each tool's optional fields; null or "" in those is dropped.
    """
    optional_fields = optional_fields or {}
    choice = completion.choices[0]
    stop_reason = _STOP_REASONS.get(choice.finish_reason, choice.finish_reason)
    content: list[SimpleNamespace] = []

    calls = choice.message.tool_calls or []
    final = next((call for call in calls if call.function.name == ANSWER_TOOL), None)
    if final is not None:
        # The answer tool ends the turn; any other call made alongside it is dropped.
        stop_reason = "end_turn"
        content.append(SimpleNamespace(type="text", text=_answer_json(final.function.arguments)))
    elif stop_reason == "tool_use":
        for call in calls:
            content.append(
                SimpleNamespace(
                    type="tool_use",
                    id=call.id,
                    name=call.function.name,
                    input=_drop_empty(
                        _arguments(call.function.arguments),
                        optional_fields.get(call.function.name, set()),
                    ),
                )
            )
    else:
        content.append(SimpleNamespace(type="text", text=_answer_json(choice.message.content)))

    usage = completion.usage
    return SimpleNamespace(
        content=content,
        stop_reason=stop_reason,
        usage=SimpleNamespace(
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        ),
        _request_id=getattr(completion, "id", None),
    )


def _arguments(raw: str | None) -> Any:
    # A malformed call goes to the tool as it is, so the tool reports the error to the model.
    try:
        return json.loads(raw or "{}")
    except ValueError:
        return raw


def _drop_empty(arguments: Any, optional: set[str]) -> Any:
    if not isinstance(arguments, dict):
        return arguments
    return {
        key: value
        for key, value in arguments.items()
        if not (key in optional and value in (None, ""))
    }


def _answer_json(raw: str | None) -> str:
    """The answer as the JSON object `run_chat` expects, even if wrapped or plain prose."""
    raw = (raw or "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            if isinstance(data, dict) and "text" in data:
                return json.dumps(data)
        except ValueError:
            pass
    return json.dumps({"text": raw, "product_ids": []})
