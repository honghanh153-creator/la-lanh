from tests.daily.test_daily_api import _date_only_client


def test_daily_note_voice_defaults_to_direct_and_roast_is_read_time_only() -> None:
    client, headers = _date_only_client()
    try:
        direct = client.get("/v1/daily-note")
        explicit_direct = client.get("/v1/daily-note?voice=direct")
        roast = client.get("/v1/daily-note?voice=roast")
        direct_again = client.get("/v1/daily-note")

        assert direct.status_code == explicit_direct.status_code == roast.status_code == 200
        assert explicit_direct.json() == direct.json() == direct_again.json()
        assert all(
            response.headers["cache-control"] == "no-store, max-age=0"
            for response in (direct, explicit_direct, roast)
        )
        plain = direct.json()["reading_projection"]["active"]
        voiced = roast.json()["reading_projection"]["active"]
        assert voiced["revision_id"] == plain["revision_id"]
        assert voiced["sections"]["hook"] != plain["sections"]["hook"]
        assert voiced["sections"]["micro_action"].endswith(plain["sections"]["micro_action"])
        assert plain["sections"]["manifestation"] in voiced["sections"]["manifestation"]
        assert voiced["evidence"] == plain["evidence"]
        assert voiced["disclaimer"] == plain["disclaimer"]
        assert client.get("/v1/daily-note?voice=savage").status_code == 422

        # Sharing freezes the stored direct revision, never the presentation voice.
        share = client.post(
            f"/v1/daily-note/{direct.json()['id']}/share-artifacts",
            json={"revision_id": plain["revision_id"], "background_lens": "auto"},
            headers=headers,
        )
        assert share.status_code == 200
        assert share.json()["safe_snapshot"]["title"] == plain["sections"]["hook"]

        operation = client.get("/openapi.json").json()["paths"]["/v1/daily-note"]["get"]
        voice_parameter = next(item for item in operation["parameters"] if item["name"] == "voice")
        assert voice_parameter["in"] == "query"
        assert voice_parameter["required"] is False
    finally:
        client.__exit__(None, None, None)


def test_context_projection_accepts_roast_voice_without_changing_meaning() -> None:
    client, headers = _date_only_client()
    try:
        direct = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "work"},
            headers=headers,
        )
        roast = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "work", "voice": "roast"},
            headers=headers,
        )
        explicit_direct = client.post(
            "/v1/daily-note/context",
            json={"background_lens": "work", "voice": "direct"},
            headers=headers,
        )

        assert direct.status_code == roast.status_code == explicit_direct.status_code == 200
        assert explicit_direct.json() == direct.json()
        assert roast.headers["cache-control"] == "no-store, max-age=0"
        assert roast.json()["scope_key"] == direct.json()["scope_key"]
        plain = direct.json()["active"]["sections"]
        voiced = roast.json()["active"]["sections"]
        assert voiced["hook"] != plain["hook"]
        assert voiced["micro_action"].endswith(plain["micro_action"])
        assert roast.json()["active"]["evidence"] == direct.json()["active"]["evidence"]
        assert (
            client.post(
                "/v1/daily-note/context",
                json={"background_lens": "work", "voice": "savage"},
                headers=headers,
            ).status_code
            == 422
        )
    finally:
        client.__exit__(None, None, None)
