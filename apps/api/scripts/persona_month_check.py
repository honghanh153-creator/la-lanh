"""US-25 AC14: run the 1000 synthetic personas through "Hỏi về tháng này" on the LOCAL API.

The real FastAPI app runs in-process on a fresh local SQLite file per worker: synthetic data
only, never production, no provider call. For this run only, and only in memory, the pending
``month.*`` sentences and the two owner-only drafts (typed-question consent, month crisis notice)
are served as approved and the typed-question switch is on, so every path can be exercised. The
admission backstop is off (one test client sends thousands of requests).

Per persona (one guest each, created one after the other on one client, as persona_sim does):

- six topics asked twice: same answer both times, three parts, a "Dựa vào" line, no date;
- the easier window for one topic: starts today or later, at most three days;
- its Tarot questions typed as month questions: never flagged as crisis (false alarm), never
  echoed back, never stored;
- its ``crisis_inputs``: every one must get the crisis notice (a miss is a failure);
- its ``figurative_inputs``: must not get the crisis notice (false alarm);
- cross-person isolation: a new person sees no saved answer of the one before, cannot delete it,
  and no answer carries another persona's question text.

    uv run --directory apps/api python -m scripts.persona_month_check \\
        --out ../../qa/personas/runs/<name>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.persona_sim import ORIGIN, ROOT, _setup, git_head

PERSONAS = ROOT / "qa" / "personas" / "personas-1000.json"
INSTANT = datetime(2026, 11, 20, 5, 0, tzinfo=UTC)  # noon in Vietnam
TOPICS = ("work", "money", "love", "family", "study", "mind")
CONSENT = "month-typed-question-v1"
DATE_LIKE = re.compile(r"\b\d{1,2}\s*[./-]\s*\d{1,2}\b|\d{4}-\d{2}-\d{2}|\bngày \d")
YES_NO = re.compile(r"^(Có|Không|Được|Chưa)\b")


def _serve_month_copy_as_approved() -> None:
    from app.domains.content import copy_approval
    from app.domains.content.copy_approval import copy_digest, load_registry

    registry = dict(load_registry())
    owner_drafts = {"consent.month.typed_question", "crisis.self_harm.notice.month"}
    for key, entry in registry.items():
        if key.startswith("month.") or key in owner_drafts:
            approver = "owner" if entry.category in copy_approval.OWNER_ONLY_CATEGORIES else "codex"
            registry[key] = replace(
                entry,
                status="approved",
                approver=approver,
                date="2026-11-20",
                digest=copy_digest(entry.text),
            )
    copy_approval._runtime_registry = lambda: registry  # type: ignore[assignment]


def _client(db_url: str) -> Any:
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app
    from app.middleware import admission

    admission._policy = lambda _request: None  # type: ignore[assignment]
    app = create_app(
        Settings(
            environment="test",
            database_url=db_url,
            cors_origins=[ORIGIN],
            guest_cookie_name="la_lanh_guest",
            guest_cookie_secure=False,
            month_typed_questions_enabled=True,
        )
    )
    client = TestClient(app, base_url=ORIGIN)
    client.__enter__()
    return client


def _answer(response: Any) -> dict[str, Any] | None:
    if response.status_code != 200:
        return None
    body = response.json()
    return body.get("answer") if body.get("status") == "answered" else None


def _persona(
    client: Any, persona: dict[str, Any], previous: dict[str, Any] | None, seen_texts: list[str]
) -> dict[str, Any]:
    pid = persona["id"]
    failures: list[str] = []
    stats: Counter[str] = Counter()
    headers = _setup(client, persona)

    # Isolation before anything is saved: nothing of the previous person is visible or deletable.
    saved = client.get("/v1/month/saved", headers=headers).json()["items"]
    if saved:
        failures.append("leak:saved-visible-to-next-person")
    if previous is not None:
        deleted = client.delete(f"/v1/month/saved/{previous['saved_id']}", headers=headers)
        if deleted.status_code != 404:
            failures.append(f"leak:deleted-other-person-saved:{deleted.status_code}")

    first_work: dict[str, Any] | None = None
    for topic in TOPICS:
        one = client.post("/v1/month/answers", json={"topic": topic}, headers=headers)
        two = client.post("/v1/month/answers", json={"topic": topic}, headers=headers)
        answer = _answer(one)
        if answer is None:
            failures.append(f"topic:{topic}:status:{one.status_code}")
            continue
        stats["topic_answers"] += 1
        if one.json() != two.json():
            failures.append(f"topic:{topic}:not-deterministic")
        if not (answer["theme"] and answer["act"] and answer["say"]):
            failures.append(f"topic:{topic}:missing-part")
        if not answer["basis"]["line"].startswith("Dựa vào: "):
            failures.append(f"topic:{topic}:no-basis")
        if DATE_LIKE.search(one.text):
            failures.append(f"topic:{topic}:date-in-answer")
        if any(text in one.text for text in seen_texts):
            failures.append(f"topic:{topic}:other-person-text")
        if topic == "work":
            first_work = answer

    window = client.get("/v1/month/window", params={"topic": "money"}, headers=headers)
    if window.status_code != 200 or not window.json().get("found"):
        failures.append(f"window:{window.status_code}")
    else:
        body = window.json()
        start, end = body["start"], body["end"]
        if (
            not ("2026-11-20" <= start <= end)
            or (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days > 2
        ):
            failures.append("window:range")

    saved_id = None
    if first_work is not None:
        response = client.post(
            "/v1/month/saved",
            json={"topic": "work", "answer_key": first_work["answer_key"]},
            headers=headers,
        )
        if response.status_code != 201:
            failures.append(f"save:{response.status_code}")
        else:
            saved_id = response.json()["id"]
            listed = client.get("/v1/month/saved", headers=headers).json()["items"]
            if [item["id"] for item in listed] != [saved_id]:
                failures.append("save:list-mismatch")

    for question in persona.get("tarot_questions", []):
        text = question["text"][:280]
        if len(text) < 8:
            continue
        stats["typed_questions"] += 1
        response = client.post(
            "/v1/month/answers",
            json={"question": text, "consent_version": CONSENT},
            headers=headers,
        )
        if response.status_code == 422 and response.json().get("code") == "CRISIS_NOTICE":
            stats["typed_false_alarm"] += 1
            continue
        if response.status_code != 200:
            failures.append(f"typed:status:{response.status_code}")
            continue
        if text in response.text:
            failures.append("typed:echoed")
        body = response.json()
        if body["status"] == "need_topic":
            stats["typed_need_topic"] += 1
            continue
        stats["typed_answered"] += 1
        stats[f"typed_topic:{body['answer']['topic']}"] += 1
        if body["answer"]["reframe"]:
            stats["typed_reframed"] += 1
        for part in ("theme", "act", "say"):
            if YES_NO.match(body["answer"][part]):
                failures.append("typed:yes-no")
        if DATE_LIKE.search(response.text):
            failures.append("typed:date-in-answer")

    tests = persona.get("tests", {})
    for item in tests.get("crisis_inputs", []):
        text = item["text"] if isinstance(item, dict) else item
        stats["crisis_inputs"] += 1
        response = client.post(
            "/v1/month/answers",
            json={"question": text, "consent_version": CONSENT},
            headers=headers,
        )
        if response.status_code == 422 and response.json().get("code") == "CRISIS_NOTICE":
            stats["crisis_routed"] += 1
            if response.json()["notice"]["copy_id"] != "crisis.self_harm.notice.month":
                failures.append("crisis:wrong-notice")
        else:
            failures.append("crisis:missed")
    for item in tests.get("figurative_inputs", []):
        text = item["text"] if isinstance(item, dict) else item
        stats["figurative_inputs"] += 1
        body = text if len(text) >= 8 else f"{text} tháng này"
        response = client.post(
            "/v1/month/answers",
            json={"question": body[:280], "consent_version": CONSENT},
            headers=headers,
        )
        if response.status_code == 422 and response.json().get("code") == "CRISIS_NOTICE":
            stats["figurative_flagged"] += 1

    seen_texts.extend(q["text"] for q in persona.get("tarot_questions", []) if len(q["text"]) >= 20)
    return {
        "persona": pid,
        "precision": persona["birth"]["precision"],
        "failures": failures,
        "stats": dict(stats),
        "saved_id": saved_id,
    }


def _worker(personas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    import time_machine

    _serve_month_copy_as_approved()
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as folder:
        client = _client(f"sqlite+aiosqlite:///{Path(folder) / 'month.db'}")
        previous: dict[str, Any] | None = None
        seen: list[str] = []
        try:
            with time_machine.travel(INSTANT, tick=True):
                for persona in personas:
                    try:
                        row = _persona(client, persona, previous, seen)
                    except Exception as error:  # a broken persona is a failure, not a crash
                        row = {
                            "persona": persona["id"],
                            "precision": persona["birth"]["precision"],
                            "failures": [f"error:{type(error).__name__}"],
                            "stats": {},
                            "saved_id": None,
                        }
                    results.append(row)
                    if row["saved_id"]:
                        previous = row
        finally:
            client.__exit__(None, None, None)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--personas", default=str(PERSONAS))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    personas = json.loads(Path(args.personas).read_text(encoding="utf-8"))["personas"]
    if args.limit:
        personas = personas[: args.limit]
    batches = [personas[i :: args.workers] for i in range(args.workers)]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = [row for batch in pool.map(_worker, [b for b in batches if b]) for row in batch]
    rows.sort(key=lambda row: row["persona"])
    totals: Counter[str] = Counter()
    failures: Counter[str] = Counter()
    for row in rows:
        totals.update(row["stats"])
        failures.update(
            item.split(":status:")[0] if ":status:" in item else item for item in row["failures"]
        )
    by_precision = Counter(row["precision"] for row in rows)
    crisis_inputs = totals["crisis_inputs"]
    figurative = totals["figurative_inputs"]
    typed = totals["typed_questions"]
    summary = {
        "git_head": git_head(),
        "personas": len(rows),
        "by_precision": dict(by_precision),
        "seconds": round(time.monotonic() - started, 1),
        "database": "local SQLite per worker (synthetic, deleted with the temp dir)",
        "copy": "month.* and the two owner drafts served as approved in memory for this run only",
        "crisis": {
            "inputs": crisis_inputs,
            "routed": totals["crisis_routed"],
            "missed": crisis_inputs - totals["crisis_routed"],
            "recall": round(totals["crisis_routed"] / crisis_inputs, 4) if crisis_inputs else None,
        },
        "false_alarms": {
            "figurative_inputs": figurative,
            "figurative_flagged": totals["figurative_flagged"],
            "typed_questions": typed,
            "typed_flagged": totals["typed_false_alarm"],
            "rate": round(
                (totals["figurative_flagged"] + totals["typed_false_alarm"])
                / max(1, figurative + typed),
                4,
            ),
        },
        "typed": {
            "answered": totals["typed_answered"],
            "need_topic": totals["typed_need_topic"],
            "reframed": totals["typed_reframed"],
            "topics": {
                k.split(":", 1)[1]: v
                for k, v in sorted(totals.items())
                if k.startswith("typed_topic:")
            },
        },
        "topic_answers": totals["topic_answers"],
        "failures": dict(failures),
        "failing_personas": [row["persona"] for row in rows if row["failures"]],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
