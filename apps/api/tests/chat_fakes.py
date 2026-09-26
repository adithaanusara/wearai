"""A scripted stand-in for the model, so chat tests need no network and cost nothing."""

import copy
import json
from types import SimpleNamespace
from typing import Any


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_use(name: str, arguments: Any, call_id: str = "toolu_1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=call_id, name=name, input=arguments)


def block(kind: str, **fields: Any) -> SimpleNamespace:
    return SimpleNamespace(type=kind, **fields)


def message(
    content: list[Any],
    stop_reason: str | None = "end_turn",
    input_tokens: int = 100,
    output_tokens: int = 50,
    request_id: str = "req_test",
) -> SimpleNamespace:
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )
    return SimpleNamespace(
        content=content, stop_reason=stop_reason, usage=usage, _request_id=request_id
    )


def answer(text: str, product_ids: list[str] | None = None, **kwargs: Any) -> SimpleNamespace:
    payload = json.dumps({"text": text, "product_ids": product_ids or []})
    return message([text_block(payload)], **kwargs)


def calling(*calls: SimpleNamespace, **kwargs: Any) -> SimpleNamespace:
    return message(list(calls), stop_reason="tool_use", **kwargs)


class ScriptedGateway:
    """Plays back prepared responses, in order, and records every request it receives."""

    def __init__(self, *script: Any) -> None:
        self.script = list(script)
        self.requests: list[dict[str, Any]] = []

    def create(self, **params: Any) -> Any:
        # Copied now, because the caller keeps adding to the same message list.
        self.requests.append(copy.deepcopy(params))
        if not self.script:
            raise AssertionError("The model was called more often than the test expected")
        step = self.script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step
