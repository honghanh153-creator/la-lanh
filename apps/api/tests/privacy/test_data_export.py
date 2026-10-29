"""POST /v1/session/data-export: the owner's own data file (right of access / portability)."""

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from app.domains.data_export.models import DataExport
from tests.radar.test_flow import ORIGIN, _client, _full_profile

EXPORT = "/v1/session/data-export"


def _headers(csrf: str) -> dict[str, str]:
    return {"Origin": ORIGIN, "X-CSRF-Token": csrf}


def _populate_owner(owner: TestClient, csrf: str) -> dict[str, Any]:
    """A with a full profile, a Daily note (mood, saved, shared), Tarot and both Radar modes."""
    headers = _headers(csrf)
    note = owner.get("/v1/daily-note")
    assert note.status_code == 200
    note_id = note.json()["id"]
    assert (
        owner.put(
            f"/v1/daily-note/{note_id}/mood", headers=headers, json={"mood": "Chill"}
        ).status_code
        == 200
    )
    assert owner.put(f"/v1/daily-note/{note_id}/saved", headers=headers).status_code in {200, 201}
    share = owner.post(
        f"/v1/daily-note/{note_id}/share-artifacts", headers=headers, json={"format": "square_1_1"}
    )
    assert share.status_code == 200
    tarot = owner.post(
        "/v1/tarot/sessions",
        headers=headers,
        json={
            "context": "relationships",
            "question": "Mình nên nhìn rõ điều gì trước khi nhắn lại?",
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": "export-tarot-start-1234567890",
        },
    )
    assert tarot.status_code == 201
    assert owner.post("/v1/identity/claim", headers=headers).status_code == 200
    private = owner.post(
        "/v1/radar/private-checks",
        headers=headers,
        json={
            "recipient_label": "Người hay seen",
            "context": "crush",
            "voice": "playful_grounded",
            "birth_date": "1996-07-21",
            "birth_time_local": "19:40",
            "place_id": "vn-dak-lak",
            "consent_version": "radar-authorized-input-v1",
            "authorization_attested": True,
        },
    )
    assert private.status_code == 200
    invite = owner.post(
        "/v1/radar/requests", headers=headers, json={"recipient_label": "Mèo", "context": "friend"}
    )
    assert invite.status_code == 200
    return {
        "note": note.json(),
        "share": share.json(),
        "tarot": tarot.json(),
        "invite_token": invite.json()["share_url"].rsplit("/", 1)[-1],
        "invite_id": invite.json()["id"],
    }


def _accept_as_recipient(owner: TestClient, request_id: str, token: str) -> tuple[TestClient, str]:
    recipient = TestClient(owner.app, base_url=ORIGIN)
    assert recipient.get(f"/v1/public/radar/{token}").status_code == 200
    csrf = _full_profile(recipient, "export-recipient-guest-1234567", "1996-07-21", "19:40")
    accepted = recipient.post(
        "/v1/public/radar/current/accept",
        headers=_headers(csrf),
        json={"request_id": request_id, "consent_version": "radar-pair-v1"},
    )
    assert accepted.status_code == 200
    return recipient, csrf


def _walk(value: object) -> list[tuple[str, object]]:
    pairs: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            pairs.append((str(key), item))
            pairs.extend(_walk(item))
    elif isinstance(value, list):
        for item in value:
            pairs.extend(_walk(item))
    return pairs


def test_owner_downloads_own_data_without_credentials_or_other_peoples_data(
    tmp_path: Path,
) -> None:
    with _client(tmp_path / "export.db") as owner:
        csrf = _full_profile(owner, "export-owner-guest-1234567890", "1994-03-12", "08:15")
        made = _populate_owner(owner, csrf)
        recipient, recipient_csrf = _accept_as_recipient(
            owner, made["invite_id"], made["invite_token"]
        )

        response = owner.post(EXPORT, headers=_headers(csrf))
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store, max-age=0"
        assert response.headers["pragma"] == "no-cache"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["content-disposition"] == (
            'attachment; filename="la-lanh-du-lieu-cua-toi.json"'
        )
        body = response.json()
        DataExport.model_validate(body)  # strict schema: no unexpected field

        birth = body["birth_profile"]
        assert birth["birth_date"] == "1994-03-12"
        assert birth["birth_time_mode"] == "exact"
        assert birth["birth_time_local"] == "08:15"
        assert birth["place_display_name"] and birth["timezone_id"] == "Asia/Ho_Chi_Minh"
        assert birth["calculation_kind"] == "natal_chart"
        purposes = {consent["purpose"] for consent in body["consents"]}
        assert "birth_profile_basic" in purposes

        [daily] = body["daily_notes"]
        assert daily["title"] == made["note"]["title"]
        assert daily["mood"] == "Chill"
        [saved] = body["saved_notes"]
        assert saved["title"] == made["note"]["title"]
        [share] = body["share_links"]
        assert share["status"] == "active" and share["format"] == "square_1_1"
        [tarot] = body["tarot_sessions"]
        assert tarot["question"] == "Mình nên nhìn rõ điều gì trước khi nhắn lại?"

        sent = {item["nickname"]: item for item in body["radar_sent"]}
        assert set(sent) == {"Người hay seen", "Mèo"}
        assert sent["Người hay seen"]["mode"] == "private_check"
        assert sent["Người hay seen"]["permission_attested_at"] is not None
        assert sent["Mèo"]["status"] == "completed"
        assert body["radar_received"] == []

        text = response.text
        # Never a credential, capability, hash or internal id.
        for secret in (
            csrf,
            made["invite_token"],
            made["invite_id"],
            made["note"]["id"],
            made["tarot"]["id"],
            made["share"]["id"],
        ):
            assert secret not in text
        if made["share"].get("token"):
            assert made["share"]["token"] not in text
        for cookie in owner.cookies.jar:
            assert cookie.value is None or cookie.value not in text
        forbidden_keys = {"id", "token", "token_hash", "csrf_token", "receipt", "guest_id"}
        assert not forbidden_keys & {key for key, _ in _walk(body)}
        suspicious = {
            key for key, _ in _walk(body) if key.endswith(("_id", "_hash", "_ciphertext"))
        }
        assert suspicious <= {"timezone_id", "config_hash"}, suspicious
        # B's birth data (the private check input and B's own profile) never appears.
        assert "1996-07-21" not in text
        # No Radar result prose leaves the app through the file.
        assert "compatibility_map" not in text and "sections" not in json.dumps(body["radar_sent"])

        # B exports B's own side: consent and dates, never the nickname A typed for B.
        received = recipient.post(EXPORT, headers=_headers(recipient_csrf))
        assert received.status_code == 200
        received_body = received.json()
        [item] = received_body["radar_received"]
        assert item["consent_version"] == "radar-pair-v1" and item["context"] == "friend"
        assert "Mèo" not in received.text and "Người hay seen" not in received.text
        assert received_body["radar_sent"] == []
        assert received_body["birth_profile"]["birth_date"] == "1996-07-21"
        assert "1994-03-12" not in received.text


def test_export_requires_the_session_csrf_and_a_trusted_origin(tmp_path: Path) -> None:
    # Five rejected attempts: rejected calls count against the per-peer limit too.
    with _client(tmp_path / "export-auth.db") as owner:
        csrf = _full_profile(owner, "export-auth-guest-1234567890", "1994-03-12", "08:15")
        anonymous = TestClient(owner.app, base_url=ORIGIN)
        other = TestClient(owner.app, base_url=ORIGIN)
        other_csrf = _full_profile(other, "export-other-guest-1234567890", "1990-01-02", "06:30")

        assert anonymous.post(EXPORT, headers=_headers(csrf)).status_code in {401, 403}
        rejected = owner.post(EXPORT, headers={"Origin": ORIGIN})
        assert rejected.status_code == 403
        assert rejected.headers["cache-control"] == "no-store, max-age=0"
        assert "1994" not in rejected.text
        assert owner.post(EXPORT, headers=_headers(other_csrf)).status_code == 403
        hostile = owner.post(
            EXPORT, headers={"Origin": "https://evil.example", "X-CSRF-Token": csrf}
        )
        assert hostile.status_code == 403
        assert owner.post(EXPORT, headers={"X-CSRF-Token": csrf}).status_code == 403
        assert owner.get(EXPORT).status_code == 405


def test_another_guest_gets_only_their_own_file(tmp_path: Path) -> None:
    with _client(tmp_path / "export-other.db") as owner:
        csrf = _full_profile(owner, "export-mine-guest-1234567890", "1994-03-12", "08:15")
        other = TestClient(owner.app, base_url=ORIGIN)
        other_csrf = _full_profile(other, "export-other-guest-1234567890", "1990-01-02", "06:30")
        mine = owner.post(EXPORT, headers=_headers(csrf))
        theirs = other.post(EXPORT, headers=_headers(other_csrf))
        assert mine.status_code == theirs.status_code == 200
        assert mine.json()["birth_profile"]["birth_date"] == "1994-03-12"
        assert theirs.json()["birth_profile"]["birth_date"] == "1990-01-02"
        assert "1994-03-12" not in theirs.text and "1990-01-02" not in mine.text


def test_export_is_a_fresh_read_after_deletion(tmp_path: Path) -> None:
    with _client(tmp_path / "export-fresh.db") as owner:
        csrf = _full_profile(owner, "export-fresh-guest-1234567890", "1994-03-12", "08:15")
        first = owner.post(EXPORT, headers=_headers(csrf)).json()
        assert first["birth_profile"]["birth_time_local"] == "08:15"
        removed = owner.request(
            "DELETE",
            "/v1/birth-profile/supplement",
            headers=_headers(csrf),
            json={"remove_time": True, "remove_place": True},
        )
        assert removed.status_code in {200, 204}
        second = owner.post(EXPORT, headers=_headers(csrf)).json()
        assert second["birth_profile"]["birth_time_local"] is None
        assert second["birth_profile"]["place_display_name"] is None
        assert second["birth_profile"]["birth_time_mode"] == "unknown"


def test_export_is_rate_limited_per_peer(tmp_path: Path) -> None:
    with _client(tmp_path / "export-limit.db") as owner:
        csrf = _full_profile(owner, "export-limit-guest-1234567890", "1994-03-12", "08:15")
        statuses = [owner.post(EXPORT, headers=_headers(csrf)).status_code for _ in range(6)]
        assert statuses[:5] == [200] * 5
        assert statuses[5] == 429
        limited = owner.post(EXPORT, headers=_headers(csrf))
        assert limited.status_code == 429
        assert limited.headers["retry-after"]
        assert limited.headers["cache-control"].startswith("no-store")


def test_export_bounds_each_list_and_says_so(tmp_path: Path) -> None:
    with _client(tmp_path / "export-bound.db") as owner:
        csrf = _full_profile(owner, "export-bound-guest-1234567890", "1994-03-12", "08:15")
        headers = _headers(csrf)
        for index in range(3):
            assert (
                owner.post(
                    "/v1/tarot/sessions",
                    headers=headers,
                    json={
                        "context": "relationships",
                        "question": "Mình nên nhìn rõ điều gì trước khi nhắn lại?",
                        "spread": "one_card",
                        "origin": "direct",
                        "idempotency_key": f"export-bound-tarot-{index}-1234567890",
                    },
                ).status_code
                == 201
            )
        service = cast(Any, owner.app).state.data_export_service
        service._max_items = 2
        body = owner.post(EXPORT, headers=headers).json()
        assert len(body["tarot_sessions"]) == 2
        assert body["truncated"] == ["tarot_sessions"]


def test_export_keeps_the_apps_history_visibility(tmp_path: Path) -> None:
    database = tmp_path / "export-history.db"
    with _client(database) as owner:
        csrf = _full_profile(owner, "export-history-guest-1234567890", "1994-03-12", "08:15")
        headers = _headers(csrf)
        assert (
            owner.post(
                "/v1/session/history-retention",
                headers=headers,
                json={"consent_version": "history-retention-v1"},
            ).status_code
            == 200
        )
        note = owner.get("/v1/daily-note")
        assert note.status_code == 200
        assert len(owner.post(EXPORT, headers=headers).json()["daily_notes"]) == 1

        # Two days later the unsaved note is hidden in the app, so the file leaves it out too.
        with sqlite3.connect(database) as connection:
            shift = timedelta(days=2)
            note_id = note.json()["id"].replace("-", "")
            note_date, created_at = connection.execute(
                "SELECT note_date, created_at FROM daily_notes WHERE id = ?", (note_id,)
            ).fetchone()
            connection.execute(
                "UPDATE daily_notes SET note_date = ?, created_at = ? WHERE id = ?",
                (
                    (date.fromisoformat(note_date) - shift).isoformat(),
                    (datetime.fromisoformat(created_at) - shift).isoformat(sep=" "),
                    note_id,
                ),
            )
            (activated_at,) = connection.execute(
                "SELECT activated_at FROM history_retention_policies"
            ).fetchone()
            connection.execute(
                "UPDATE history_retention_policies SET activated_at = ?",
                ((datetime.fromisoformat(activated_at) - shift).isoformat(sep=" "),),
            )
        body = owner.post(EXPORT, headers=headers).json()
        assert body["daily_notes"] == []
        assert body["history_retention"]["consent_version"] == "history-retention-v1"


def test_guest_without_birth_profile_gets_an_empty_file(tmp_path: Path) -> None:
    with _client(tmp_path / "export-empty.db") as client:
        created = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "export-empty-guest-1234567890",
            },
        )
        assert created.status_code == 200
        body = client.post(EXPORT, headers=_headers(created.json()["csrf_token"])).json()
        assert body["birth_profile"] is None and body["account"] is None
        assert body["matching"] is None and body["radar_sent"] == []
        assert body["not_included"] and body["truncated"] == []
