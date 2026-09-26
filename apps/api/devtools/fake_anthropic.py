"""A FAKE Anthropic API for local development. It is not part of the product and is never used in
production. It costs nothing and needs no key.

It speaks the real wire format, so the whole chat path runs for real: the SDK, the tool loop, the
store's tools and database, the limits and the endpoint. Only the "thinking" is fake: it picks a
tool from keywords and words the answer from the tool's real result. Every answer ends with a
marker so nobody mistakes it for the real assistant.

    pnpm dev:fake-ai      # this server, on http://127.0.0.1:9999
    pnpm dev:api:fake     # the API, pointed at it (overrides any real key in .env)

Special words for testing: REFUSE makes it refuse, DOWN makes it fail with a 500.
"""

import argparse
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

MARKER = " [dev fake AI]"
MODEL = "claude-opus-5"

_CATEGORY_WORDS = {
    "hoodie": "hoodies",
    "legging": "leggings",
    "tee": "t-shirts",
    "t-shirt": "t-shirts",
    "shirt": "t-shirts",
    "short": "shorts",
    "jogger": "joggers",
    "bag": "bags",
    "duffel": "bags",
    "cap": "caps",
    "sock": "socks",
    "bottle": "bottles",
}
_COLOURS = ("black", "white", "grey", "gray", "charcoal", "stone", "off white")
_BROWSE_WORDS = ("show", "browse", "recommend", "products", "shop", "what do you have", "suggest")
_GREETINGS = ("hi", "hello", "hey", "good morning", "good afternoon", "good evening")

# Checked in this order, so "can I pay cash on delivery" is about payment, not delivery.
_TOPICS = [
    ("returns", ("return", "exchange", "refund")),
    ("payment", ("pay", "cash", "card", "bank transfer")),
    ("delivery", ("deliver", "shipping", "ship ", "postage")),
    ("sizing", ("size", "sizing", "fit", "measure")),
    ("contact", ("contact", "email", "phone", "call you", "opening hours", "hours")),
]


def _message(content: list[dict[str, Any]], stop_reason: str) -> dict[str, Any]:
    return {
        "id": "msg_devfake",
        "type": "message",
        "role": "assistant",
        "model": MODEL,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 800, "output_tokens": 80},
    }


def _answer(text: str, product_ids: list[str] | None = None) -> dict[str, Any]:
    payload = {"text": text + MARKER, "product_ids": product_ids or []}
    return _message([{"type": "text", "text": json.dumps(payload)}], "end_turn")


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    block = {"type": "tool_use", "id": f"toolu_{name}", "name": name, "input": arguments}
    return _message([block], "tool_use")


def _customer_question(messages: list[dict[str, Any]]) -> str:
    """The latest thing the customer typed (tool results also arrive as user messages)."""
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(message["content"], str):
            return message["content"]
    return ""


def _search_arguments(question: str) -> dict[str, Any] | None:
    text = question.lower()
    arguments: dict[str, Any] = {}

    category = next(
        (c for word, c in _CATEGORY_WORDS.items() if re.search(rf"\b{word}", text)), None
    )
    if category:
        arguments["category"] = category
    if re.search(r"\bwomen|\bladies|\bwoman", text):
        arguments["gender"] = "women"
    elif re.search(r"\bmen\b|\bmens\b|\bman\b", text):
        arguments["gender"] = "men"
    if re.search(r"\bsale\b|discount|reduced|offer|cheap", text):
        arguments["on_sale"] = True
    if re.search(r"\bnew\b|latest|arrival", text):
        arguments["new_only"] = True
    if price := re.search(r"(?:under|below|less than|max)\s*(?:lkr\s*)?([\d,]{3,})", text):
        arguments["max_price"] = int(price.group(1).replace(",", ""))
    if colour := next((c for c in _COLOURS if c in text), None):
        arguments["query"] = colour

    if arguments or any(word in text for word in _BROWSE_WORDS):
        return arguments
    return None


def _first_step(question: str) -> dict[str, Any]:
    text = question.lower()
    for topic, words in _TOPICS:
        if any(word in text for word in words):
            return _call("get_store_info", {"topic": topic})
    if (arguments := _search_arguments(question)) is not None:
        return _call("search_products", arguments)
    if any(text.strip().startswith(greeting) for greeting in _GREETINGS):
        return _answer(
            "Hello! I can help you find products, choose a size, or answer questions "
            "about delivery, payment and returns."
        )
    return _answer(
        "I can only help with our products, sizes, delivery, payment and returns. "
        "What would you like to know?"
    )


def _words_for_topic(topic: str, info: dict[str, Any]) -> str:
    if topic == "delivery":
        parts = []
        for method in info["methods"]:
            fee = "free" if method["fee"] == "free" else method["fee"]
            free_from = method["free_when_order_is_at_least"]
            extra = f", free on orders of {free_from} or more" if free_from else ""
            parts.append(f"{method['name']} is {fee}{extra} ({method['estimated_time']})")
        return "; ".join(parts) + "."
    if topic == "payment":
        return "You can pay by " + ", ".join(m["name"].lower() for m in info["methods"]) + "."
    if topic == "sizing":
        return info["advice"] + " Measurements are in the size guide on each product page."
    if topic == "returns":
        return (
            f"You can return or exchange items within {info['return_window_days']} days. "
            f"{info['conditions']} {info['how_to_start']}"
        )
    return f"You can email {info['email']} or call {info['phone']} ({info['hours']})."


def _finish(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Words the answer from the tool result that just came back."""
    call = next(
        block
        for message in reversed(messages)
        if message["role"] == "assistant" and isinstance(message["content"], list)
        for block in message["content"]
        if block.get("type") == "tool_use"
    )
    results = messages[-1]["content"]
    if any(result.get("is_error") for result in results):
        return _answer("Sorry, I couldn't look that up just now. Please try again.")
    data = json.loads(results[0]["content"])

    if call["name"] == "get_store_info":
        return _answer(_words_for_topic(call["input"]["topic"], data))

    products = data.get("products", [])
    if not products:
        return _answer(
            "I couldn't find anything matching that. Try different words, or ask me "
            "to show what's new or on sale."
        )
    shown = products[:3]
    lines = [f"{p['name']} in {p['colour']} ({p['price']})" for p in shown]
    return _answer("Here are some options: " + "; ".join(lines) + ".", [p["id"] for p in shown])


def respond(body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """The fake's whole brain: a request body in, a status and response body out."""
    messages = body["messages"]
    question = _customer_question(messages)

    if "REFUSE" in question:
        return 200, _message([], "refusal")
    if "DOWN" in question:
        return 500, {"type": "error", "error": {"type": "api_error", "message": "dev fake outage"}}

    last = messages[-1]
    if last["role"] == "user" and isinstance(last["content"], list):
        return 200, _finish(messages)
    return 200, _first_step(question)


class _Handler(BaseHTTPRequestHandler):
    delay = 0.0

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - the base class's name
        pass

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        # A real model takes a moment, and the typing indicator should be visible in development.
        time.sleep(self.delay)
        status, payload = respond(body)
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("request-id", "req_devfake")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(port: int = 9999, delay: float = 0.0) -> ThreadingHTTPServer:
    # Loopback only: this is a development tool and must not be reachable from other machines.
    handler = type("Handler", (_Handler,), {"delay": delay})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A fake Anthropic API for local development")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--delay", type=float, default=0.8, help="seconds to wait before answering")
    args = parser.parse_args()
    server = make_server(args.port, args.delay)
    print(f"Dev fake AI listening on http://127.0.0.1:{server.server_port} (not for production)")
    server.serve_forever()
