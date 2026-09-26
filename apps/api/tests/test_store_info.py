import pytest

from app.checkout_data import DELIVERY_METHODS, PAYMENT_METHODS
from app.formatting import format_lkr
from app.store_info import SIZE_CHART, TOPICS, store_info


def test_format_lkr_matches_the_website() -> None:
    assert format_lkr(4450) == "LKR 4,450.00"
    assert format_lkr(125000) == "LKR 125,000.00"
    assert format_lkr(0) == "LKR 0.00"


def test_delivery_facts_come_from_the_same_data_as_the_checkout() -> None:
    methods = {m["name"]: m for m in store_info("delivery")["methods"]}

    for method in DELIVERY_METHODS.values():
        entry = methods[method.label]
        assert entry["estimated_time"] == method.estimate
        assert entry["fee"] == ("free" if method.fee == 0 else format_lkr(method.fee))
    standard = methods["Standard delivery"]
    assert (standard["fee"], standard["free_when_order_is_at_least"]) == (
        "LKR 450.00",
        "LKR 15,000.00",
    )
    assert methods["Express delivery"]["free_when_order_is_at_least"] is None


def test_changing_the_delivery_data_changes_what_the_assistant_says(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    monkeypatch.setitem(
        DELIVERY_METHODS, "standard", replace(DELIVERY_METHODS["standard"], fee=600)
    )

    fees = [m["fee"] for m in store_info("delivery")["methods"]]

    assert "LKR 600.00" in fees and "LKR 450.00" not in fees


def test_payment_methods_are_listed() -> None:
    names = [m["name"] for m in store_info("payment")["methods"]]

    assert names == [m.label for m in PAYMENT_METHODS.values()]


def test_sizing_has_the_whole_chart_and_advice() -> None:
    info = store_info("sizing")

    assert info["measurements_cm"] == SIZE_CHART and len(SIZE_CHART) == 5
    assert "larger" in info["advice"]


def test_returns_and_contact() -> None:
    returns, contact = store_info("returns"), store_info("contact")

    assert returns["return_window_days"] == 14 and "unworn" in returns["conditions"]
    assert contact["email"] in returns["how_to_start"]
    assert set(contact) == {"email", "phone", "hours"}


def test_every_topic_is_answerable() -> None:
    for topic in TOPICS:
        assert store_info(topic)  # type: ignore[arg-type]
