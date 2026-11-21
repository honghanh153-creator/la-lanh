"""Returning users across a release: the same personas, database and history, two app versions.

Phase 1 runs ``persona_sim``'s day loop on one checkout (the old release) for N days and keeps
the per-worker SQLite files plus each persona's guest cookie in ``--state``. Phase 2 runs on a
second checkout (the new release, or a candidate) against a COPY of that state, continuing the
same clock: day numbers, dates and idempotency keys go on from where phase 1 stopped. Both
phases use this file and the scoring of the checkout that runs it; copy the new release's
harness into the old checkout so only the app code differs.

    # phase 1, old app code
    python -m scripts.persona_switch --phase 1 --personas P.json --state S --out O1 \
        --start 2026-10-22 --days 29
    # phase 2, new app code, same people (copy S first if several phase-2 variants share it)
    python -m scripts.persona_switch --phase 2 --personas P.json --state S --out O2 \
        --start 2026-10-22 --offset 29 --days 29

Local temporary SQLite only, synthetic personas only, no network, generation off. Mood and the
crisis / figurative / Tarot inputs repeat on the persona's 29-day cycle (``day % 29``), so phase 2
tests crisis routing again. On phase 1 some days are also saved (``--save-every``) so phase 2 can
check that saved notes, the kept action, moods and Tarot sessions from before the switch still
open; the result is ``carryover`` in the first phase-2 row of each persona.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts import persona_sim as sim

CYCLE = 29


def _instant(start: date, day: int, minute: int = 0) -> datetime:
    return datetime(start.year, start.month, start.day, 5, minute, tzinfo=UTC) + timedelta(days=day)


def _inputs(persona: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    inputs: dict[int, list[dict[str, Any]]] = {}
    for q in persona.get("tarot_questions", []):
        inputs.setdefault(q["day"], []).append({**q, "kind": "question"})
    for c in persona["tests"]["crisis_inputs"]:
        inputs.setdefault(c["day"], []).append({**c, "kind": "crisis", "context": "self_care"})
    for f in persona["tests"]["figurative_inputs"]:
        inputs.setdefault(f["day"], []).append({**f, "kind": "figurative", "context": "general"})
    return inputs


def _carryover(client: Any, headers: dict[str, str], memo: dict[str, Any]) -> dict[str, Any]:
    """Open what the person left in phase 1, on the phase-2 code. Statuses and counts only."""

    out: dict[str, Any] = {}
    saved = client.get("/v1/saved-notes")
    out["saved_status"] = saved.status_code
    items = saved.json() if saved.status_code == 200 else []
    out["saved_expected"] = len(memo.get("saved", []))
    out["saved_found"] = len(items) if isinstance(items, list) else 0
    found_ids = {str(i.get("daily_note_id")) for i in items} if isinstance(items, list) else set()
    out["saved_missing"] = len([n for n in memo.get("saved", []) if n not in found_ids])
    out["saved_without_text"] = sum(
        1
        for i in (items if isinstance(items, list) else [])
        if not (i.get("note_snapshot") or i.get("reading_snapshot"))
    )
    held = client.get("/v1/daily-note/experiment")
    out["kept_status"] = held.status_code
    body = held.json() if held.status_code == 200 and held.content else None
    out["kept_expected"] = bool(memo.get("kept"))
    out["kept_found"] = isinstance(body, dict) and bool(body.get("id"))
    # A saved note keeps its mood; an unsaved note older than its day is gone with its mood
    # (Codex auto-1 on #781). Expect the first, count the second separately.
    saved_ids = set(memo.get("saved", []))
    mooded = memo.get("mooded", [])
    kept_moods = [n for n in mooded if n in saved_ids][-5:]
    gone_moods = [n for n in mooded[:-1] if n not in saved_ids][-5:]
    moods = [client.get(f"/v1/daily-note/{n}/mood") for n in kept_moods]
    out["mood_statuses"] = sorted({m.status_code for m in moods})
    out["mood_found"] = sum(1 for m in moods if m.status_code == 200 and m.content and m.json())
    out["mood_expected"] = len(moods)
    older = [client.get(f"/v1/daily-note/{n}/mood") for n in gone_moods]
    out["mood_expired_expected"] = len(older)
    out["mood_expired_still_open"] = sum(
        1 for m in older if m.status_code == 200 and m.content and m.json()
    )
    tarot = [client.get(f"/v1/tarot/sessions/{s}") for s in memo.get("tarot", [])[-3:]]
    out["tarot_statuses"] = sorted({t.status_code for t in tarot})
    out["tarot_expected"] = len(tarot)
    out["tarot_found"] = sum(1 for t in tarot if t.status_code == 200)
    retention = client.get("/v1/session/history-retention")
    out["retention_status"] = retention.status_code
    overview = client.get("/v1/insights/overview")
    out["overview_status"] = overview.status_code
    out["any_5xx"] = any(
        s >= 500
        for s in [
            saved.status_code,
            held.status_code,
            retention.status_code,
            overview.status_code,
            *[m.status_code for m in moods],
            *[m.status_code for m in older],
            *[t.status_code for t in tarot],
        ]
    )
    return out


def run_persona(
    persona: dict[str, Any],
    db_url: str,
    labels: dict[str, str],
    state: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    import time_machine

    from scripts.persona_metrics import is_light, keeps_action, norm, signals

    reactions = sim.mood_reactions()
    pid = persona["id"]
    inputs = _inputs(persona)
    start = date.fromisoformat(args.start)
    memo: dict[str, Any] = state.setdefault(
        pid, {"saved": [], "notes": [], "mooded": [], "tarot": [], "kept": False}
    )
    rows: list[dict[str, Any]] = []
    with time_machine.travel(_instant(start, args.offset), tick=False):
        client = sim._client(db_url)
        if args.phase == 1:
            headers = sim._setup(client, persona)
            memo["csrf"] = headers["X-CSRF-Token"]
        else:
            headers = {"Origin": sim.ORIGIN, "X-CSRF-Token": memo["csrf"]}
            for name, value in memo["cookies"].items():
                client.cookies.set(name, value)
    try:
        for k in range(args.days):
            day = args.offset + k
            cyc = day % CYCLE
            mood = persona["mood_29"][cyc]
            row: dict[str, Any] = {
                "persona": pid,
                "day": day,
                "phase": args.phase,
                "date": (start + timedelta(days=day)).isoformat(),
                "mood": mood,
            }
            if args.phase == 2 and k == 0:
                with time_machine.travel(_instant(start, day, 0), tick=False):
                    row["carryover"] = _carryover(client, headers, memo)
            with time_machine.travel(_instant(start, day, 1), tick=False):
                sim._LAST_ISSUE[0] = None
                first = client.get("/v1/daily-note")
                row["status"] = first.status_code
                row["situation"] = sim._LAST_ISSUE[0]
                if first.status_code != 200:
                    row["error"] = first.json().get("code") if first.content else None
                    rows.append(row)
                    continue
                note = first.json()
                row["before_mood"] = {
                    "headline": sim._section(note, "hook"),
                    "action": sim._section(note, "micro_action"),
                }
            with time_machine.travel(_instant(start, day, 2), tick=False):
                put = client.put(
                    f"/v1/daily-note/{note['id']}/mood", json={"mood": mood}, headers=headers
                )
                row["mood_status"] = put.status_code
                saved = put.json() if put.status_code == 200 and put.content else None
                saved_mood = saved.get("mood") if isinstance(saved, dict) else None
            with time_machine.travel(_instant(start, day, 3), tick=False):
                again = client.get("/v1/daily-note")
                if again.status_code == 200:
                    note = again.json()
                if row["situation"] is None:
                    row["situation"] = sim._LAST_ISSUE[0]
            memo["notes"].append(str(note["id"]))
            if put.status_code == 200:
                memo.setdefault("mooded", []).append(str(note["id"]))
            active = ((note.get("reading_projection") or {}).get("active")) or {}
            view = sim.shown_action(active, saved_mood)
            experiment = view["experiment"]
            row.update(
                headline=sim._section(note, "hook"),
                thesis=sim._section(note, "thesis"),
                scene=sim._section(note, "manifestation"),
                action=view["action"],
                la_line=sim._section(note, "companion"),
                why_today=sim._section(note, "transit"),
                mood_reaction=reactions.get(mood),
                persona_mode=note.get("persona_mode"),
                source_level=note.get("source_level"),
                mode=active.get("mode"),
                action_weight=view["weight"],
                experiment_offered=experiment is not None,
                lighter_offered=view["lighter_offered"],
                lighter_shown=view["lighter_shown"],
                card_action=sim._section(note, "micro_action"),
                saved_mood=saved_mood,
            )
            shown = " ".join(
                str(row.get(k2) or "")
                for k2 in ("headline", "thesis", "scene", "action", "la_line", "why_today")
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
                with time_machine.travel(_instant(start, day, 4), tick=False):
                    held = client.get("/v1/daily-note/experiment")
                    held_body = held.json() if held.status_code == 200 and held.content else None
                    replace = (
                        {
                            "expected_experiment_id": held_body["id"],
                            "expected_version": held_body["version"],
                        }
                        if isinstance(held_body, dict) and held_body.get("id")
                        else {}
                    )
                    kept = client.put(
                        f"/v1/daily-note/{note['id']}/experiment",
                        json={
                            "revision_id": active["revision_id"],
                            "background_lens": "auto",
                            "action_key": experiment["action_key"],
                            "consent_version": "action-experiment-v1",
                            **replace,
                        },
                        headers=headers,
                    )
                row["keep_status"] = kept.status_code
                row["kept"] = kept.status_code == 200
                memo["kept"] = memo["kept"] or row["kept"]
            if args.save_every and day % args.save_every == 0:
                with time_machine.travel(_instant(start, day, 4), tick=False):
                    body = (
                        {"revision_id": active["revision_id"]} if active.get("revision_id") else {}
                    )
                    sv = client.put(
                        f"/v1/daily-note/{note['id']}/saved", json=body, headers=headers
                    )
                row["save_status"] = sv.status_code
                if sv.status_code in (200, 201):
                    memo["saved"].append(str(note["id"]))
            rows.append(row)
            with time_machine.travel(_instant(start, day, 5), tick=False):
                tarot_rows = []
                for item in inputs.get(cyc, []):
                    item = {**item, "text": item["text"]}
                    rec = sim._tarot(client, headers, pid, day, item)
                    tarot_rows.append(rec)
                row["tarot"] = tarot_rows
            memo["tarot"].extend(t["session_id"] for t in tarot_rows if t.get("session_id"))
    finally:
        memo["cookies"] = {c.name: c.value for c in client.cookies.jar}
        client.__exit__(None, None, None)
    return rows


def _install_tarot_id() -> None:
    """Record the Tarot session id the persona created, so phase 2 can reopen it."""

    original = sim._tarot

    def wrapped(client: Any, headers: Any, pid: str, day: int, item: Any) -> dict[str, Any]:
        seen: list[str] = []
        post = client.post

        def spy(url: str, *a: Any, **kw: Any) -> Any:
            response = post(url, *a, **kw)
            if url == "/v1/tarot/sessions" and response.status_code == 201:
                seen.append(str(response.json().get("id")))
            return response

        client.post = spy
        try:
            record = original(client, headers, pid, day, item)
        finally:
            client.post = post
        if seen:
            record["session_id"] = seen[0]
        return record

    sim._tarot = wrapped


def _worker(job: tuple[int, list[dict[str, Any]], str]) -> list[dict[str, Any]]:
    index, batch, raw_args = job
    args = argparse.Namespace(**json.loads(raw_args))
    sim._install_pick_observer()
    _install_tarot_id()
    labels = sim._labels()
    state_dir = Path(args.state)
    db_url = f"sqlite+aiosqlite:///{state_dir}/worker-{index}.db"
    state_file = state_dir / f"worker-{index}.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    out: list[dict[str, Any]] = []
    for persona in batch:
        started = time.monotonic()
        try:
            rows = run_persona(persona, db_url, labels, state, args)
        except Exception as error:  # one broken persona must not hide the others
            detail = getattr(getattr(error, "response", None), "text", "") or str(error)
            rows = [
                {
                    "persona": persona["id"],
                    "day": args.offset + k,
                    "phase": args.phase,
                    "mood": persona["mood_29"][(args.offset + k) % CYCLE],
                    "status": 0,
                    "error": f"{type(error).__name__}: {detail[:200]}",
                }
                for k in range(args.days)
            ]
        out.extend(rows)
        print(
            f"{persona['id']} {len(rows)} days {time.monotonic() - started:.1f}s",
            file=sys.stderr,
            flush=True,
        )
    state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=int, choices=(1, 2), required=True)
    parser.add_argument("--personas", required=True)
    parser.add_argument("--state", required=True, help="folder with worker DBs + cookies")
    parser.add_argument("--out", required=True)
    parser.add_argument("--start", default="2026-10-22")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--days", type=int, default=29)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--save-every", type=int, default=7)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    state_dir = Path(args.state)
    state_dir.mkdir(parents=True, exist_ok=True)
    meta_path = state_dir / "state-meta.json"
    if args.phase == 1:
        if any(state_dir.glob("worker-*.db")):
            raise SystemExit("phase 1 needs an empty --state folder")
        meta_path.write_text(json.dumps({"workers": args.workers, "start": args.start}) + "\n")
    else:
        saved_meta = json.loads(meta_path.read_text())
        args.workers = saved_meta["workers"]  # same batches, same DB per persona
        args.start = saved_meta["start"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    personas = json.loads(Path(args.personas).read_text(encoding="utf-8"))["personas"]
    if args.only:
        personas = [p for p in personas if p["id"] in set(args.only)]
    batches = [personas[i :: args.workers] for i in range(args.workers)]
    raw = json.dumps(vars(args))
    started = time.monotonic()
    jobs = [(i, b, raw) for i, b in enumerate(batches) if b]
    with ProcessPoolExecutor(max_workers=len(jobs)) as pool:
        results = [row for batch in pool.map(_worker, jobs) for row in batch]
    results.sort(key=lambda r: (r["persona"], r["day"]))
    with (out / "transcript.jsonl").open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "git_head": sim.git_head(),
        "phase": args.phase,
        "start": (date.fromisoformat(args.start) + timedelta(days=args.offset)).isoformat(),
        "offset": args.offset,
        "days": args.days,
        "personas": len(personas),
        "rows": len(results),
        "seconds": round(time.monotonic() - started, 1),
        "database": "local SQLite per worker, carried from phase 1 (synthetic)",
        "generation": "off (Settings default); no provider call",
        "daily_variety_from": sim.PRODUCTION_DAILY_VARIETY_FROM.isoformat(),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    main()
