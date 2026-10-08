from datetime import datetime

from fastapi.testclient import TestClient

from app.config import Settings
from app.domains.experiments.service import ExperimentService
from app.main import create_app


def _date_only_client() -> tuple[TestClient, dict[str, str]]:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    client = TestClient(app, base_url="http://127.0.0.1:5173")
    client.__enter__()
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "idempotency_key": "daily-context-1234567890",
        },
    )
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "X-CSRF-Token": guest.json()["csrf_token"],
    }
    assert (
        client.post(
            "/v1/birth-profile",
            json={"birth_date": "1990-01-01"},
            headers=headers,
        ).status_code
        == 200
    )
    return client, headers


def test_context_projection_uses_private_body_and_get_stays_context_free() -> None:
    client, headers = _date_only_client()
    try:
        automatic = client.get("/v1/daily-note")
        query_attempt = client.get("/v1/daily-note?background_lens=relationships")
        contextual = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "relationships"},
            headers=headers,
        )
        explicit_auto = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "auto"},
            headers=headers,
        )

        assert (
            automatic.status_code
            == query_attempt.status_code
            == contextual.status_code
            == explicit_auto.status_code
            == 200
        )
        assert query_attempt.json() == automatic.json()
        assert explicit_auto.json() == automatic.json()["reading_projection"]
        assert contextual.json()["scope_key"] != automatic.json()["reading_projection"]["scope_key"]
        assert (
            contextual.json()["active"]["evidence"]
            == (automatic.json()["reading_projection"]["active"]["evidence"])
        )
        assert (
            contextual.json()["active"]["sections"]["manifestation"]
            != (automatic.json()["reading_projection"]["active"]["sections"]["manifestation"])
        )
        assert (
            contextual.json()["active"]["sections"]["micro_action"]
            != (automatic.json()["reading_projection"]["active"]["sections"]["micro_action"])
        )
        assert all(
            response.headers["cache-control"] == "no-store, max-age=0"
            for response in (automatic, query_attempt, contextual)
        )

        operation = client.get("/openapi.json").json()["paths"]["/v1/daily-note"]["get"]
        assert all(item["name"] != "background_lens" for item in operation["parameters"])
    finally:
        client.__exit__(None, None, None)


def test_context_projection_requires_origin_csrf_and_closed_enum_body() -> None:
    client, headers = _date_only_client()
    try:
        assert (
            client.post(
                "/v1/daily-note/context",
                json={"background_lens": "work"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/v1/daily-note/context",
                json={"background_lens": "work"},
                headers={**headers, "X-CSRF-Token": "wrong"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/v1/daily-note/context",
                json={"background_lens": "career"},
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/v1/daily-note/context",
                json={"background_lens": "work", "free_text": "secret"},
                headers=headers,
            ).status_code
            == 422
        )
    finally:
        client.__exit__(None, None, None)


def test_daily_response_refreshes_from_vibe_to_aura_without_birth_pii() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "daily-metadata-1234567890",
            },
        )
        csrf_token = guest.json()["csrf_token"]
        headers = {"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": csrf_token}
        assert (
            client.post(
                "/v1/birth-profile", json={"birth_date": "1990-01-01"}, headers=headers
            ).status_code
            == 200
        )

        vibe = client.get("/v1/daily-note")
        assert vibe.status_code == 200
        assert vibe.json()["persona_mode"] == "vibe"
        vibe_projection = vibe.json()["reading_projection"]
        assert vibe_projection["active"]["mode"] == "vibe_fallback"
        assert vibe_projection["active"]["sections"]["transit"] is None
        assert vibe_projection["available_update"] is None

        supplement = client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "exact",
                "birth_time_local": "08:15",
                "place_id": "vn-hanoi",
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        )
        assert supplement.status_code == 200

        aura = client.get("/v1/daily-note")
        assert aura.status_code == 200
        payload = aura.json()
        assert payload["id"] == vibe.json()["id"]
        assert payload["persona_mode"] == "aura"
        assert payload["source_level"] == "natal_chart"
        assert payload["persona_version"] == "persona-v2"
        assert payload["content_version"] == "daily-note-v4"
        assert payload["fallback_used"] is False
        assert payload["fallback_reason"] is None
        assert payload["awakening"] is not None
        assert len(payload["awakening"]["factors"]) >= 3
        assert payload["sky_chapter"] is not None
        assert payload["sky_chapter"]["phase"] in {"approaching", "exact", "separating"}
        assert payload["title"] != vibe.json()["title"]
        assert 80 <= len(payload["full_body"].split()) <= 140
        projection = payload["reading_projection"]
        assert projection["active"]["revision_id"] == vibe_projection["active"]["revision_id"]
        assert projection["active"]["mode"] == "vibe_fallback"
        assert projection["available_update"]["message"] == ("Có một bản đọc mới đang chờ bạn")
        assert projection["available_update"]["content"]["mode"] == "full_synthesis"
        transition_id = projection["aura_transition"]["transition_id"]
        assert transition_id is not None

        rejected_origin = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": transition_id},
            headers={"X-CSRF-Token": csrf_token},
        )
        assert rejected_origin.status_code == 403

        rejected_acknowledgement = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": transition_id},
            headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": "wrong"},
        )
        assert rejected_acknowledgement.status_code == 403

        stale_acknowledgement = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": "f" * 64},
            headers=headers,
        )
        assert stale_acknowledgement.status_code == 409
        assert stale_acknowledgement.json()["code"] == "AURA_TRANSITION_CONFLICT"

        acknowledged = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": transition_id},
            headers=headers,
        )
        assert acknowledged.status_code == 200
        assert acknowledged.headers["cache-control"] == "no-store, max-age=0"
        assert acknowledged.json()["aura_transition"]["acknowledged"] is True

        refreshed_acknowledgement = client.get("/v1/daily-note")
        assert refreshed_acknowledgement.status_code == 200
        assert (
            refreshed_acknowledgement.json()["reading_projection"]["aura_transition"][
                "acknowledged"
            ]
            is True
        )

        rejected_activation = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": projection["available_update"]["revision_id"]},
            headers={"Origin": "http://127.0.0.1:5173", "X-CSRF-Token": "wrong"},
        )
        assert rejected_activation.status_code == 403

        stale_activation = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": projection["active"]["revision_id"]},
            headers=headers,
        )
        assert stale_activation.status_code == 409

        first_guest_cookie = client.cookies.get("la_lanh_guest")
        client.cookies.clear()
        other_guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "daily-other-guest-1234567890",
            },
        )
        other_headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": other_guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile",
                json={"birth_date": "1991-02-02"},
                headers=other_headers,
            ).status_code
            == 200
        )
        wrong_guest = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": projection["available_update"]["revision_id"]},
            headers=other_headers,
        )
        assert wrong_guest.status_code == 409
        assert wrong_guest.json()["code"] == "READING_UPDATE_CONFLICT"
        wrong_guest_acknowledgement = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": transition_id},
            headers=other_headers,
        )
        assert wrong_guest_acknowledgement.status_code == 409
        assert wrong_guest_acknowledgement.json()["code"] == "AURA_TRANSITION_CONFLICT"

        client.cookies.clear()
        assert first_guest_cookie is not None
        client.cookies.set("la_lanh_guest", first_guest_cookie)

        activated = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": projection["available_update"]["revision_id"]},
            headers=headers,
        )
        assert activated.status_code == 200
        assert activated.json()["active"]["mode"] == "full_synthesis"
        assert activated.json()["available_update"] is None

        after_activation = client.get("/v1/daily-note")
        assert after_activation.status_code == 200
        assert after_activation.json()["reading_projection"] == activated.json()

        assert after_activation.json()["sky_chapter"] == payload["sky_chapter"]

        serialized = str(payload)
        for forbidden in (
            "birth_date",
            "birth_time",
            "birth_place",
            "latitude",
            "longitude",
            "guest_token",
            "1990-01-01",
            "08:15",
            "Hà Nội",
            csrf_token,
            "gate_policy_version",
            "renderer_version",
            "publishable_candidate",
        ):
            assert forbidden not in serialized


def test_new_aura_transition_identity_is_not_acknowledged() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "aura-transition-identity-1234",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile",
                json={"birth_date": "1990-01-01"},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/v1/daily-note").status_code == 200

        def supplement_at(local_time: str) -> None:
            response = client.post(
                "/v1/birth-profile/supplement",
                json={
                    "birth_time_mode": "exact",
                    "birth_time_local": local_time,
                    "place_id": "vn-hanoi",
                    "consent_version": "birth-profile-deep-v1",
                },
                headers=headers,
            )
            assert response.status_code == 200

        supplement_at("08:15")
        first = client.get("/v1/daily-note").json()["reading_projection"]
        first_transition_id = first["aura_transition"]["transition_id"]
        assert first_transition_id is not None
        acknowledged = client.put(
            f"/v1/reading-projections/{first['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": first_transition_id},
            headers=headers,
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["aura_transition"]["acknowledged"] is True

        supplement_at("09:15")
        second = client.get("/v1/daily-note").json()["reading_projection"]
        assert second["aura_transition"]["transition_id"] != first_transition_id
        assert second["aura_transition"]["acknowledged"] is False

        stale = client.put(
            f"/v1/reading-projections/{second['scope_key']}/aura-transition/acknowledge",
            json={"transition_id": first_transition_id},
            headers=headers,
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "AURA_TRANSITION_CONFLICT"


def test_approximate_birth_time_never_unlocks_sky_chapter() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "daily-approximate-1234567890",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile", json={"birth_date": "1990-01-01"}, headers=headers
            ).status_code
            == 200
        )
        supplement = client.post(
            "/v1/birth-profile/supplement",
            json={
                "birth_time_mode": "approx_window",
                "birth_time_local": None,
                "approx_window": "morning",
                "place_id": "vn-hanoi",
                "consent_version": "birth-profile-deep-v1",
            },
            headers=headers,
        )
        assert supplement.status_code == 200
        assert supplement.json()["time_precision"] == "approximate"

        note = client.get("/v1/daily-note")

        assert note.status_code == 200
        assert note.json()["persona_mode"] == "vibe"
        assert note.json()["awakening"] is None
        assert note.json()["sky_chapter"] is None
        projection = note.json()["reading_projection"]
        assert projection["active"]["mode"] == "limited"
        assert projection["active"]["precision"] == "approximate"
        assert projection["active"]["sections"]["transit"] is None


def test_experiment_api_is_server_owned_cas_protected_and_reflectable() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "daily-experiment-1234567890",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile",
                json={"birth_date": "1990-01-01"},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/v1/daily-note").status_code == 200
        assert (
            client.post(
                "/v1/birth-profile/supplement",
                json={
                    "birth_time_mode": "exact",
                    "birth_time_local": "08:15",
                    "place_id": "vn-hanoi",
                    "consent_version": "birth-profile-deep-v1",
                },
                headers=headers,
            ).status_code
            == 200
        )

        note = client.get("/v1/daily-note").json()
        projection = note["reading_projection"]
        activated = client.put(
            f"/v1/reading-projections/{projection['scope_key']}/activate",
            json={"expected_revision_id": projection["available_update"]["revision_id"]},
            headers=headers,
        )
        assert activated.status_code == 200
        active = activated.json()["active"]
        experiment = active["experiment"]
        body = {
            "revision_id": active["revision_id"],
            "background_lens": "auto",
            "action_key": experiment["action_key"],
            "consent_version": "action-experiment-v1",
        }

        assert client.put(f"/v1/daily-note/{note['id']}/experiment", json=body).status_code == 403
        assert (
            client.put(
                f"/v1/daily-note/{note['id']}/experiment",
                json={**body, "action": "client-authored text"},
                headers=headers,
            ).status_code
            == 422
        )
        assert (
            client.put(
                f"/v1/daily-note/{note['id']}/experiment",
                json={**body, "action_key": "0" * 64},
                headers=headers,
            ).status_code
            == 404
        )
        assert client.get("/v1/daily-note/experiment").json() is None
        chosen = client.put(
            f"/v1/daily-note/{note['id']}/experiment",
            json=body,
            headers=headers,
        )
        assert chosen.status_code == 200
        assert chosen.headers["cache-control"] == "no-store, max-age=0"
        chosen_payload = chosen.json()
        assert chosen_payload["state"] == "chosen"
        assert chosen_payload["outcome"] is None
        assert chosen_payload["action"] == experiment["action"]
        assert chosen_payload["observation"] == experiment["observation"]
        assert chosen_payload["permission"] == experiment["permission"]
        assert (
            datetime.fromisoformat(chosen_payload["expires_at"])
            - datetime.fromisoformat(chosen_payload["created_at"])
            == ExperimentService.RETENTION_WINDOW
        )
        assert (
            client.put(
                f"/v1/daily-note/{note['id']}/experiment",
                json=body,
                headers=headers,
            ).json()
            == chosen_payload
        )
        assert client.get("/v1/daily-note/experiment").json() == chosen_payload

        undone = client.request(
            "DELETE",
            "/v1/daily-note/experiment",
            json={
                "experiment_id": chosen_payload["id"],
                "expected_version": chosen_payload["version"],
            },
            headers=headers,
        )
        assert undone.status_code == 204
        assert client.get("/v1/daily-note/experiment").json() is None
        chosen_payload = client.put(
            f"/v1/daily-note/{note['id']}/experiment",
            json=body,
            headers=headers,
        ).json()

        contextual = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "work"},
            headers=headers,
        ).json()["active"]
        replacement = {
            "revision_id": contextual["revision_id"],
            "background_lens": "work",
            "action_key": contextual["experiment"]["action_key"],
            "consent_version": "action-experiment-v1",
        }
        replace_required = client.put(
            f"/v1/daily-note/{note['id']}/experiment",
            json=replacement,
            headers=headers,
        )
        assert replace_required.status_code == 409

        replaced = client.put(
            f"/v1/daily-note/{note['id']}/experiment",
            json={
                **replacement,
                "expected_experiment_id": chosen_payload["id"],
                "expected_version": chosen_payload["version"],
            },
            headers=headers,
        )
        assert replaced.status_code == 200
        replaced_payload = replaced.json()
        assert replaced_payload["id"] != chosen_payload["id"]
        assert replaced_payload["version"] == chosen_payload["version"] + 1

        stale = client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": chosen_payload["id"],
                "expected_version": chosen_payload["version"],
                "outcome": "helpful",
            },
            headers=headers,
        )
        assert stale.status_code == 409

        reflected = client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": replaced_payload["id"],
                "expected_version": replaced_payload["version"],
                "outcome": "not_for_now",
            },
            headers=headers,
        )
        assert reflected.status_code == 200
        assert reflected.json()["state"] == "reflected"
        assert reflected.json()["outcome"] == "not_for_now"
        assert client.get("/v1/daily-note/experiment").json() is None
        for _ in range(3):
            replay = client.put(
                f"/v1/daily-note/{note['id']}/experiment",
                json=replacement,
                headers=headers,
            )
            assert replay.status_code == 409
        assert client.get("/v1/daily-note/experiment").json() is None


def test_experiment_is_deleted_when_exact_birth_input_changes() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            cors_origins=["http://127.0.0.1:5173"],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    with TestClient(app, base_url="http://127.0.0.1:5173") as client:
        guest = client.post(
            "/v1/guest-sessions",
            json={
                "consent_version": "birth-profile-v1",
                "purpose": "birth_profile_basic",
                "idempotency_key": "stale-daily-experiment-1234567890",
            },
        )
        headers = {
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        assert (
            client.post(
                "/v1/birth-profile",
                json={"birth_date": "1990-01-01"},
                headers=headers,
            ).status_code
            == 200
        )
        assert client.get("/v1/daily-note").status_code == 200

        def supplement(time: str, place_id: str) -> None:
            response = client.post(
                "/v1/birth-profile/supplement",
                json={
                    "birth_time_mode": "exact",
                    "birth_time_local": time,
                    "place_id": place_id,
                    "consent_version": "birth-profile-deep-v1",
                },
                headers=headers,
            )
            assert response.status_code == 200

        def activate_and_choose() -> dict[str, object]:
            note = client.get("/v1/daily-note").json()
            projection = note["reading_projection"]
            activated = client.put(
                f"/v1/reading-projections/{projection['scope_key']}/activate",
                json={"expected_revision_id": projection["available_update"]["revision_id"]},
                headers=headers,
            )
            assert activated.status_code == 200
            active = activated.json()["active"]
            experiment = active["experiment"]
            chosen = client.put(
                f"/v1/daily-note/{note['id']}/experiment",
                json={
                    "revision_id": active["revision_id"],
                    "background_lens": "auto",
                    "action_key": experiment["action_key"],
                    "consent_version": "action-experiment-v1",
                },
                headers=headers,
            )
            assert chosen.status_code == 200
            payload: dict[str, object] = chosen.json()
            return payload

        supplement("08:15", "vn-hanoi")
        hidden_by_current = activate_and_choose()
        supplement("09:20", "vn-ho-chi-minh")

        assert client.get("/v1/daily-note/experiment").json() is None
        deleted_outcome = client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": hidden_by_current["id"],
                "expected_version": hidden_by_current["version"],
                "outcome": "helpful",
            },
            headers=headers,
        )
        assert deleted_outcome.status_code == 409

        rejected_by_reflect = activate_and_choose()
        supplement("10:25", "vn-hanoi")

        stale_outcome = client.post(
            "/v1/daily-note/experiment/outcome",
            json={
                "experiment_id": rejected_by_reflect["id"],
                "expected_version": rejected_by_reflect["version"],
                "outcome": "helpful",
            },
            headers=headers,
        )
        assert stale_outcome.status_code == 409
        assert client.get("/v1/daily-note/experiment").json() is None
