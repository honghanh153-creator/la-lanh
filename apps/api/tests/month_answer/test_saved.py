"""Lưu is explicit, lives in its own list, can be deleted, and never crosses people (US-25 AC12)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.domains.erasure_journal.journal import ErasureKind
from app.domains.erasure_journal.tables import ErasureJournalRow
from app.domains.month_answer.tables import SavedMonthAnswerRow

from .test_api import _client, _person, _row_counts


@pytest.fixture
def client() -> Iterator[TestClient]:
    with _client() as test_client:
        yield test_client


def _answer(client: TestClient, headers: dict[str, str], topic: str = "work") -> dict[str, Any]:
    response = client.post("/v1/month/answers", json={"topic": topic}, headers=headers)
    assert response.status_code == 200, response.text
    return dict(response.json()["answer"])


def _rows(client: TestClient) -> list[SavedMonthAnswerRow]:
    app: Any = client.app

    async def read() -> list[SavedMonthAnswerRow]:
        async with app.state.database.sessions() as session:
            return list(await session.scalars(select(SavedMonthAnswerRow)))

    assert client.portal is not None
    return client.portal.call(read)


def test_save_list_delete(client: TestClient, approve_month: Callable[..., None]) -> None:
    approve_month()
    headers = _person(client, "save")
    answer = _answer(client, headers)
    assert client.get("/v1/month/saved", headers=headers).json() == {"items": []}

    saved = client.post(
        "/v1/month/saved",
        json={"topic": "work", "answer_key": answer["answer_key"]},
        headers=headers,
    )
    assert saved.status_code == 201, saved.text
    body = saved.json()
    for part in ("theme", "act", "say", "disclaimer", "topic_label"):
        assert body["answer"][part] == answer[part]
    assert body["answer"]["basis"] == answer["basis"]

    again = client.post(
        "/v1/month/saved",
        json={"topic": "work", "answer_key": answer["answer_key"]},
        headers=headers,
    )
    assert again.json()["id"] == body["id"]  # saving twice keeps one copy
    listed = client.get("/v1/month/saved", headers=headers).json()["items"]
    assert [item["id"] for item in listed] == [body["id"]]

    deleted = client.delete(f"/v1/month/saved/{body['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/v1/month/saved", headers=headers).json() == {"items": []}
    assert client.delete(f"/v1/month/saved/{body['id']}", headers=headers).status_code == 404


def test_saved_text_is_encrypted_at_rest(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "rest")
    answer = _answer(client, headers, "money")
    client.post(
        "/v1/month/saved",
        json={"topic": "money", "answer_key": answer["answer_key"]},
        headers=headers,
    )
    [row] = _rows(client)
    assert answer["theme"] not in row.snapshot_ciphertext
    assert answer["say"] not in row.snapshot_ciphertext


def test_save_takes_no_text_from_the_client(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "forged")
    forged = client.post(
        "/v1/month/saved",
        json={"topic": "work", "answer_key": "0" * 32},
        headers=headers,
    )
    assert forged.status_code == 409
    extra = client.post(
        "/v1/month/saved",
        json={"topic": "work", "answer_key": "0" * 32, "theme": "chữ lạ"},
        headers=headers,
    )
    assert extra.status_code == 422
    assert _rows(client) == []


def test_another_person_cannot_list_or_delete(approve_month: Callable[..., None]) -> None:
    approve_month()
    with _client() as client:
        owner = _person(client, "owner")
        answer = _answer(client, owner)
        saved_id = client.post(
            "/v1/month/saved",
            json={"topic": "work", "answer_key": answer["answer_key"]},
            headers=owner,
        ).json()["id"]
        # A second guest on the same client replaces the cookie: it is another person.
        other = _person(client, "other")
        assert client.get("/v1/month/saved", headers=other).json() == {"items": []}
        assert client.delete(f"/v1/month/saved/{saved_id}", headers=other).status_code == 404
        # The other person's answer key does not save the owner's answer either.
        assert len(_rows(client)) == 1


def test_delete_is_journaled_without_content(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "journal")
    answer = _answer(client, headers, "love")
    saved_id = client.post(
        "/v1/month/saved",
        json={"topic": "love", "answer_key": answer["answer_key"]},
        headers=headers,
    ).json()["id"]
    client.delete(f"/v1/month/saved/{saved_id}", headers=headers)
    app: Any = client.app

    async def read() -> list[ErasureJournalRow]:
        async with app.state.database.sessions() as session:
            return list(await session.scalars(select(ErasureJournalRow)))

    assert client.portal is not None
    entries = client.portal.call(read)
    kinds = [entry.kind for entry in entries]
    assert ErasureKind.SAVED_MONTH_ANSWER_REMOVED.value in kinds
    assert all(saved_id.encode() not in bytes(entry.subject_digest) for entry in entries)


def test_saved_answers_are_in_the_data_export(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "export")
    answer = _answer(client, headers, "study")
    client.post(
        "/v1/month/saved",
        json={"topic": "study", "answer_key": answer["answer_key"]},
        headers=headers,
    )
    export = client.post("/v1/session/data-export", headers=headers)
    assert export.status_code == 200, export.text
    [item] = export.json()["saved_month_answers"]
    assert item["theme"] == answer["theme"] and item["topic"] == "study"


def test_removing_birth_time_deletes_saved_month_answers(
    client: TestClient, approve_month: Callable[..., None]
) -> None:
    approve_month()
    headers = _person(client, "remove-time")
    answer = _answer(client, headers, "family")
    client.post(
        "/v1/month/saved",
        json={"topic": "family", "answer_key": answer["answer_key"]},
        headers=headers,
    )
    assert len(_rows(client)) == 1
    removed = client.request(
        "DELETE", "/v1/birth-profile/supplement", json={"remove_time": True}, headers=headers
    )
    assert removed.status_code in {200, 204}, removed.text
    assert _rows(client) == []


def test_asking_never_saves(client: TestClient, approve_month: Callable[..., None]) -> None:
    approve_month()
    headers = _person(client, "never")
    before = _row_counts(client)
    for topic in ("work", "money", "love"):
        _answer(client, headers, topic)
    assert _row_counts(client) == before
    assert _rows(client) == []
