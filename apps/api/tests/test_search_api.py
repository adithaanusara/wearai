import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("catalogue")


def ids(response) -> list[str]:
    return [item["id"] for item in response.json()["items"]]


def search(client: TestClient, query: str, **params: int):
    return client.get("/api/v1/search", params={"q": query, **params})


def test_empty_query_returns_nothing(client: TestClient) -> None:
    for query in ["", "   ", "!!!"]:
        body = search(client, query).json()
        assert body["items"] == [] and body["total"] == 0


def test_every_word_must_match(client: TestClient) -> None:
    assert ids(search(client, "black hoodie")) == ["m-hood-02"]
    assert search(client, "zzzz").json()["total"] == 0


def test_matching_is_case_insensitive_and_ignores_punctuation(client: TestClient) -> None:
    assert "m-hood-01" in ids(search(client, "HOODIE!!"))


def test_men_does_not_match_womens_products(client: TestClient) -> None:
    results = search(client, "men").json()["items"]

    assert len(results) == 6
    assert {item["gender"] for item in results} == {"men"}


def test_category_and_colour_words_that_are_not_in_the_name_match(client: TestClient) -> None:
    assert search(client, "leggings").json()["total"] == 3
    assert [i["colour"] for i in search(client, "stone").json()["items"]] == ["Stone"]


def test_name_matches_rank_above_other_matches(client: TestClient) -> None:
    assert ids(search(client, "cap black"))[0] == "a-cap-01"


def test_ties_keep_the_featured_order(client: TestClient) -> None:
    # "black" only matches the colour field, so every result scores the same.
    assert ids(search(client, "black")) == [
        "w-tee-01",
        "w-leg-03",
        "w-short-01",
        "m-short-01",
        "m-hood-02",
        "m-tee-02",
        "a-bag-01",
        "a-cap-01",
        "a-bottle-01",
    ]


def test_search_pagination(client: TestClient) -> None:
    first = search(client, "black", pageSize=3, page=1).json()
    second = search(client, "black", pageSize=3, page=2).json()

    assert first["total"] == second["total"] == 9
    assert len(first["items"]) == 3
    assert {i["id"] for i in first["items"]}.isdisjoint(i["id"] for i in second["items"])


def test_overlong_query_is_rejected(client: TestClient) -> None:
    assert search(client, "a" * 101).status_code == 422


def test_regex_characters_are_harmless(client: TestClient) -> None:
    response = search(client, "(*[")

    assert response.status_code == 200
    assert response.json()["total"] == 0
