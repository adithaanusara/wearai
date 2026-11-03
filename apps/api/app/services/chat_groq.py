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
        try:
            completion = self._client.chat.completions.create(**to_groq_request(params))
        except groq.APIError as error:
            # Only the kind of error is logged: no message text, and nothing that could hold a key.
            status = getattr(error, "status_code", None)
            log = logger.error if status in (400, 401, 403, 404) else logger.warning
            log("chat provider error: %s status=%s", type(error).__name__, status)
            raise ChatUnavailableError from error
        return from_groq_response(completion)


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
                _function(tool["name"], tool["description"], tool["input_schema"])
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


def from_groq_response(completion: Any) -> SimpleNamespace:
    """The completion in the shape `run_chat` reads from Anthropic."""
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
                    input=_arguments(call.function.arguments),
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
