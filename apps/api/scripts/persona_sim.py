"""Run the 100 synthetic personas through 29 simulated days against the LOCAL API.

The real FastAPI app (all routes and middleware) runs in-process over HTTP semantics with a
fresh local SQLite file per worker: synthetic data only, never production, no provider calls
(generation stays off). The date is injected with ``time_machine.travel``, the same way the
Daily API tests pin their clock (tests/daily/conftest.py). The web layer's mood reaction is
read from the web catalog file the Home screen imports, so "what the persona sees" is the API
note plus that line.

    uv run --directory apps/api python -m scripts.persona_sim --out ../../qa/personas/runs/<name>

Writes ``transcript.jsonl`` (one line per persona-day) and ``meta.json``. Score it with
``scripts.persona_report``. ``pnpm personas:run`` does both.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PERSONAS = ROOT / "qa" / "personas" / "personas-100.json"
WEB_CATALOG = ROOT / "apps" / "web" / "src" / "shared" / "ui" / "la" / "laCatalog.generated.ts"
START = date(2026, 11, 14)
DAYS = 29
ORIGIN = "http://127.0.0.1:5173"
_LAST_ISSUE: list[str | None] = [None]


def mood_reactions() -> dict[str, str]:
    """The direct-voice mood reaction lines the Home screen shows after a mood tap."""

    text = WEB_CATALOG.read_text(encoding="utf-8")
    block = text.split("export const LA_MOOD_REACTIONS", 1)[1]
    direct = block.split('"direct": {', 1)[1].split("}", 1)[0]
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', direct))


def _instant(day: int, minute: int = 0) -> datetime:
    # 12:00 Asia/Ho_Chi_Minh = 05:00 UTC; never near the 17:00 UTC rollover.
    return datetime(START.year, START.month, START.day, 5, minute, tzinfo=UTC) + timedelta(days=day)


def _key(persona_id: str, label: str) -> str:
    return hashlib.sha256(f"persona-sim\x1f{persona_id}\x1f{label}".encode()).hexdigest()[:40]


def _install_pick_observer() -> None:
    from app.domains.readings import daily_psychology

    original = daily_psychology._pick

    def observe(plan: Any, pool: list[Any]) -> Any:
        chosen = original(plan, pool)
        _LAST_ISSUE[0] = getattr(chosen, "issue_key", None)
        return chosen

    daily_psychology._pick = observe  # observe the choice, never change it


def _client(db_url: str) -> Any:
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    app = create_app(
        Settings(
            environment="test",
            database_url=db_url,
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
        )
    )
    client = TestClient(app, base_url=ORIGIN)
    client.__enter__()
    return client


def _section(note: dict[str, Any], name: str) -> str | None:
    projection = note.get("reading_projection") or {}
    sections = (projection.get("active") or {}).get("sections") or {}
    value = sections.get(name)
    return value if isinstance(value, str) else None


def _tarot(
    client: Any, headers: dict[str, str], pid: str, day: int, item: dict[str, Any]
) -> dict[str, Any]:
    from scripts.persona_metrics import crisis_routed

    record: dict[str, Any] = {"kind": item["kind"], "text": item["text"]}
    response = client.post(
        "/v1/tarot/sessions",
        json={
            "context": item.get("context", "general"),
            "question": item["text"][:280].ljust(8, "."),
            "spread": "one_card",
            "origin": "direct",
            "idempotency_key": _key(pid, f"tarot-{day}-{item['text']}"),
        },
        headers=headers,
    )
    body: Any = response.json() if response.content else None
    record["status"] = response.status_code
    record["caught"] = crisis_routed(response.status_code, body)
    if isinstance(body, dict) and "code" in body:
        record["code"] = body["code"]
    if response.status_code == 201 and isinstance(body, dict):
        session = body
        for n in range(int(session.get("required_cards", 1))):
            pick = client.put(
                f"/v1/tarot/sessions/{session['id']}/selections",
                json={"fan_index": (day * 7 + n * 11) % 78, "expected_version": session["version"]},
                headers=headers,
            )
            if pick.status_code != 200:
                record["select_status"] = pick.status_code
                break
            session = pick.json()
        reading = session.get("reading") or {}
        record["caught"] = record["caught"] or crisis_routed(200, session)
        record["headline"] = reading.get("headline")
        record["summary"] = (reading.get("summary") or "")[:400]
    return record


def _setup(client: Any, persona: dict[str, Any]) -> dict[str, str]:
    pid = persona["id"]
    guest = client.post(
        "/v1/guest-sessions",
        json={
            "consent_version": "birth-profile-v1",
            "purpose": "birth_profile_basic",
            "history_consent_version": "history-retention-v1",
            "idempotency_key": _key(pid, "guest"),
        },
    )
    guest.raise_for_status()
    headers = {"Origin": ORIGIN, "X-CSRF-Token": guest.json()["csrf_token"]}
    birth = persona["birth"]
    client.post(
        "/v1/birth-profile", json={"birth_date": birth["birth_date"]}, headers=headers
    ).raise_for_status()
    if birth["precision"] in {"exact", "approximate"}:
        places = client.post(
            "/v1/birth-places/search", json={"query": birth["birth_place"]}, headers=headers
        )
        places.raise_for_status()
        found = places.json()
        items = (
            found if isinstance(found, list) else found.get("places") or found.get("results") or []
        )
        if not items:
            raise RuntimeError(f"{pid}: synthetic place not in the local catalog")
        body: dict[str, Any] = {
            "birth_time_mode": "exact" if birth["precision"] == "exact" else "approx_window",
            "place_id": items[0]["place_id"],
            "consent_version": "birth-profile-deep-v1",
        }
        if birth["precision"] == "exact":
            body["birth_time_local"] = birth["birth_time_local"]
        else:
            body["approx_window"] = birth["approx_window"]
        client.post("/v1/birth-profile/supplement", json=body, headers=headers).raise_for_status()
    return headers


def run_persona(
    persona: dict[str, Any], db_url: str, labels: dict[str, str]
) -> list[dict[str, Any]]:
    import time_machine

    from scripts.persona_metrics import is_light, keeps_action, norm, signals

    reactions = mood_reactions()
    pid = persona["id"]
    inputs: dict[int, list[dict[str, Any]]] = {}
    for q in persona.get("tarot_questions", []):
        inputs.setdefault(q["day"], []).append({**q, "kind": "question"})
    for c in persona["tests"]["crisis_inputs"]:
        inputs.setdefault(c["day"], []).append({**c, "kind": "crisis", "context": "self_care"})
    for f in persona["tests"]["figurative_inputs"]:
        inputs.setdefault(f["day"], []).append({**f, "kind": "figurative", "context": "general"})
    rows: list[dict[str, Any]] = []
    with time_machine.travel(_instant(0), tick=False):
        client = _client(db_url)
        headers = _setup(client, persona)
    try:
        for day in range(DAYS):
            mood = persona["mood_29"][day]
            row: dict[str, Any] = {
                "persona": pid,
                "day": day,
                "date": (START + timedelta(days=day)).isoformat(),
                "mood": mood,
            }
            with time_machine.travel(_instant(day, 1), tick=False):
                _LAST_ISSUE[0] = None
                first = client.get("/v1/daily-note")
                row["status"] = first.status_code
                row["situation"] = _LAST_ISSUE[0]
                if first.status_code != 200:
                    row["error"] = first.json().get("code") if first.content else None
                    rows.append(row)
                    continue
                note = first.json()
                row["before_mood"] = {
                    "headline": _section(note, "hook"),
                    "action": _section(note, "micro_action"),
                }
            with time_machine.travel(_instant(day, 2), tick=False):
                put = client.put(
                    f"/v1/daily-note/{note['id']}/mood", json={"mood": mood}, headers=headers
                )
                row["mood_status"] = put.status_code
            with time_machine.travel(_instant(day, 3), tick=False):
                again = client.get("/v1/daily-note")
                if again.status_code == 200:
                    note = again.json()
                if row["situation"] is None:
                    row["situation"] = _LAST_ISSUE[0]
            active = ((note.get("reading_projection") or {}).get("active")) or {}
            experiment = active.get("experiment") or None
            row.update(
                headline=_section(note, "hook"),
                thesis=_section(note, "thesis"),
                scene=_section(note, "manifestation"),
                action=_section(note, "micro_action") or (experiment or {}).get("action"),
                la_line=_section(note, "companion"),
                why_today=_section(note, "transit"),
                mood_reaction=reactions.get(mood),
                legacy_title=note.get("title"),
                persona_mode=note.get("persona_mode"),
                source_level=note.get("source_level"),
                mode=active.get("mode"),
                action_weight=(experiment or {}).get("weight") or active.get("action_weight"),
                experiment_offered=experiment is not None,
            )
            shown = " ".join(
                str(row.get(k) or "")
                for k in ("headline", "thesis", "scene", "action", "la_line", "why_today")
            )
            row["return_path"], row["memory"] = signals(note, shown)
            row["action_norm"] = norm(row.get("action"))
            light, source = is_light(row.get("action"), labels, row.get("action_weight"))
            row["light"], row["light_source"] = light, source
            wants = bool(row.get("action")) and keeps_action(
                row.get("action"), light, persona, mood
            )
            row["wants_keep"], row["kept"] = wants, False
            if wants and experiment is not None and active.get("revision_id"):
                with time_machine.travel(_instant(day, 4), tick=False):
                    kept = client.put(
                        f"/v1/daily-note/{note['id']}/experiment",
                        json={
                            "revision_id": active["revision_id"],
                            "background_lens": "auto",
                            "action_key": experiment["action_key"],
                            "consent_version": "action-experiment-v1",
                        },
                        headers=headers,
                    )
                row["keep_status"] = kept.status_code
                row["kept"] = kept.status_code == 200
            rows.append(row)
            with time_machine.travel(_instant(day, 5), tick=False):
                row["tarot"] = [
                    _tarot(client, headers, pid, day, item) for item in inputs.get(day, [])
                ]
    finally:
        client.__exit__(None, None, None)
    return rows


def _worker(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _install_pick_observer()
    labels = _labels()
    out: list[dict[str, Any]] = []
    tmp = tempfile.mkdtemp(prefix="la-lanh-personas-")
    db_url = f"sqlite+aiosqlite:///{tmp}/personas-{os.getpid()}.db"
    for persona in batch:
        started = time.monotonic()
        rows = run_persona(persona, db_url, labels)
        out.extend(rows)
        print(
            f"{persona['id']} {len(rows)} days {time.monotonic() - started:.1f}s",
            file=sys.stderr,
            flush=True,
        )
    return out


def _labels() -> dict[str, str]:
    path = ROOT / "qa" / "personas" / "labels" / "action-weight.json"
    if not path.exists():
        return {}
    data: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))["labels"]
    return data


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607 - fixed argv, no shell
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--only", nargs="*", help="persona ids (debug)")
    parser.add_argument("--personas", default=str(PERSONAS))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    personas = json.loads(Path(args.personas).read_text(encoding="utf-8"))["personas"]
    if args.only:
        personas = [p for p in personas if p["id"] in set(args.only)]
    batches = [personas[i :: args.workers] for i in range(args.workers)]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = [row for batch in pool.map(_worker, [b for b in batches if b]) for row in batch]
    results.sort(key=lambda r: (r["persona"], r["day"]))
    with (out / "transcript.jsonl").open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "git_head": git_head(),
        "start": START.isoformat(),
        "days": DAYS,
        "personas": len(personas),
        "rows": len(results),
        "seconds": round(time.monotonic() - started, 1),
        "database": "local SQLite per worker (synthetic, deleted with the temp dir)",
        "clock": "time_machine.travel per call, 12:01-12:05 Asia/Ho_Chi_Minh",
        "generation": "off (Settings default); no provider call",
    }
    (out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
