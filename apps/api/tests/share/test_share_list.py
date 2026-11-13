"""US-23 share-link management: the owner lists their own links (dates, format, status) and
revokes them, including links whose Daily note is gone. Real app on SQLite, synthetic data."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.middleware.admission import _policy
from tests.saved.copy_flow import ORIGIN, delete_sources, make_app, save_and_share, start_guest

LISTED_KEYS = {"id", "format", "status", "created_at", "expires_at", "revoked_at"}


def _share(client: TestClient, headers: dict[str, str], note_id: str) -> dict[str, str]:
    response = client.post(
        f"/v1/daily-note/{note_id}/share-artifacts", json={"format": "square_1_1"}, headers=headers
    )
    assert response.status_code == 200
    body: dict[str, str] = response.json()
    return body


def test_the_owner_lists_only_their_links_without_token_or_content(tmp_path: Path) -> None:
    app = make_app(tmp_path / "list.db")
    with TestClient(app, base_url=ORIGIN) as client:
        stranger = start_guest(client)
        stranger_copies = save_and_share(client, stranger)
        client.cookies.clear()
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        second = _share(client, headers, copies.note_id)
        assert client.delete(f"/v1/share-artifacts/{second['id']}", headers=headers).status_code

        listed = client.get("/v1/share-artifacts")
        assert listed.status_code == 200
        assert listed.headers["cache-control"].startswith("no-store")
        body = listed.json()
        assert body["next_cursor"] is None
        assert [item["id"] for item in body["items"]] == [second["id"], copies.share_id]
        assert [item["status"] for item in body["items"]] == ["revoked", "active"]
        assert all(set(item) == LISTED_KEYS for item in body["items"])
        text = listed.text
        for secret in (second["token"], second["public_path"], copies.note_id, "safe_snapshot"):
            assert secret not in text
        assert stranger_copies.share_id not in text


def test_pages_are_bounded_and_the_cursor_is_checked(tmp_path: Path) -> None:
    app = make_app(tmp_path / "pages.db")
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        made = [copies.share_id] + [_share(client, headers, copies.note_id)["id"] for _ in range(2)]

        first = client.get("/v1/share-artifacts", params={"limit": 2}).json()
        assert len(first["items"]) == 2 and first["next_cursor"]
        rest = client.get(
            "/v1/share-artifacts", params={"limit": 2, "cursor": first["next_cursor"]}
        ).json()
        assert rest["next_cursor"] is None
        seen = [item["id"] for item in first["items"] + rest["items"]]
        assert sorted(seen) == sorted(made) and len(set(seen)) == 3

        for params in ({"limit": 0}, {"limit": 51}, {"cursor": "x" * 121}):
            assert client.get("/v1/share-artifacts", params=params).status_code == 422
        tampered = client.get("/v1/share-artifacts", params={"cursor": "bm90LWEtY3Vyc29y"})
        assert tampered.status_code == 422
        assert tampered.json()["code"] == "SHARE_CURSOR_INVALID"
        assert tampered.headers["cache-control"].startswith("no-store")


def test_the_list_requires_a_session(tmp_path: Path) -> None:
    app = make_app(tmp_path / "anonymous.db")
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.get("/v1/share-artifacts").status_code == 401


def test_a_detached_link_is_listed_and_revocable_and_unsave_never_revokes(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "detached-list.db"
    app = make_app(database_path)
    with TestClient(app, base_url=ORIGIN) as client:
        headers = start_guest(client)
        copies = save_and_share(client, headers)
        delete_sources(database_path)

        assert client.delete(f"/v1/daily-note/{copies.note_id}/saved", headers=headers).status_code
        listed = client.get("/v1/share-artifacts").json()["items"]
        assert [(item["id"], item["status"]) for item in listed] == [(copies.share_id, "active")]
        assert client.get(copies.public_path).status_code == 200

        revoked = client.delete(f"/v1/share-artifacts/{copies.share_id}", headers=headers)
        assert revoked.status_code == 204
        assert client.get("/v1/share-artifacts").json()["items"][0]["status"] == "revoked"
        assert client.get(copies.public_path).status_code == 404


def test_the_list_has_its_own_admission_bucket() -> None:
    class _Request:
        def __init__(self, method: str, path: str) -> None:
            self.method = method
            self.url = type("Url", (), {"path": path})()

    listed = _policy(_Request("GET", "/v1/share-artifacts"))  # type: ignore[arg-type]
    public = _policy(_Request("GET", "/v1/share-artifacts/" + "a" * 43))  # type: ignore[arg-type]
    assert listed is not None and listed.name == "share-list"
    assert public is not None and public.name == "public-capability"
