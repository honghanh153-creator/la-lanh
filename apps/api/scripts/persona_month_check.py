"""US-25 AC14: run the 1000 synthetic personas through "Hỏi về tháng này" on the LOCAL API.

The real FastAPI app runs in-process on a fresh local SQLite file per worker: synthetic data
only, never production, no provider call. For this run only, and only in memory, the pending
``month.*`` sentences are served as approved so every path can be exercised. The admission
backstop is off (one test client sends thousands of requests).

There is no typed question (owner chose AS1 on 21.11.2026). Per persona (one guest each, created
one after the other on one client, as persona_sim does):

- six topics asked twice: same answer both times, three parts, a "Dựa vào" line, no date;
- every preset question: answered with its own question and tip, the month parts equal to the
  topic answer, nothing opening like a yes/no verdict, no date;
- the easier window for one topic: starts today or later, at most three days;
- free text is refused: the persona's first Tarot question and first crisis input sent as a
  ``question`` field get a validation error and are not echoed;
- saving a topic answer and a preset answer: the list holds exactly those two;
- cross-person isolation: a new person sees no saved answer of the one before, cannot delete it,
  and no answer carries another persona's text.

It also counts, by rough keywords and for the report only, how many personas' Tarot questions
match each preset's situation: the evidence that the presets are what people wanted to ask.

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
DATE_LIKE = re.compile(r"\b\d{1,2}\s*[./-]\s*\d{1,2}\b|\d{4}-\d{2}-\d{2}|\bngày \d")
YES_NO = re.compile(r"^(Có|Không|Được|Chưa)\b")
MONTH_PARTS = ("theme", "act", "say", "basis")
# Rough situation keywords per preset, matched on the lowercased Tarot question. Report only.
PRESET_THEMES: dict[str, re.Pattern[str]] = {
    key: re.compile(pattern)
    for key, pattern in {
        "work.hard_talk": r"(sếp|quản lý|trưởng phòng).*(nói|góp ý|đề xuất|xin|trả lời)"
        r"|(nói|góp ý|đề xuất|xin).*(sếp|quản lý|trưởng phòng)",
        "work.too_much": r"deadline|dồn|nhiều việc|việc nào trước|ưu tiên|bớt việc|quá tải",
        "work.shifts": r"ca đêm|tăng ca|đổi ca|ca trực|ca tối|ca xoay|làm ca",
        "money.month_end": r"cuối tháng|hết tiền|xoay|kẹt tiền|thiếu tiền|cạn tiền|tới lương",
        "money.ask_back": r"\bđòi\b|trả tiền|\bnợ\b",
        "money.say_no": r"từ chối|không có tiền",
        "love.closer": r"gần (nhau )?hơn|ít nói chuyện|xa cách|hục hặc",
        "love.say_tired": r"(nói|kể).*mệt|hiểu mình mệt",
        "love.far": r"ở xa|yêu xa|làm xa|ít gọi|ít nhắn",
        "family.parents_ask": r"(bố|ba|mẹ).*(hỏi|giục|hối)",
        "family.my_path": r"con đường|học tiếp|ở lại .* hay về|về quê làm|muốn vẽ",
        "family.compare": r"so sánh|so mình|so với",
        "study.many_exams": r"\bôn\b|môn thi|đợt thi|thi liền|nhiều môn",
        "study.exam_energy": r"\b(thi|ôn)\b.*(mệt|sức|ngủ)|(mệt|sức|ngủ).*\b(thi|ôn)\b",
        "study.start_project": r"đồ án|ý tưởng|khóa luận|bắt đầu từ đâu",
        "mind.homesick": r"nhớ nhà",
        "mind.sleep": r"ngủ|thức khuya",
        "mind.heavy": r"nặng lòng|mệt trong lòng|buồn|trống trải|trống trống|đuối",
    }.items()
}


def _serve_month_copy_as_approved() -> None:
    from app.domains.content import copy_approval
    from app.domains.content.copy_approval import copy_digest, load_registry

    registry = dict(load_registry())
    for key, entry in registry.items():
        if key.startswith("month."):
            registry[key] = replace(
                entry,
                status="approved",
                approver="codex",
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
    by_topic: dict[str, dict[str, Any]] = {}
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
        by_topic[topic] = answer
        if topic == "work":
            first_work = answer

    presets = client.get("/v1/month/status").json().get("presets", [])
    if len(presets) != 18:
        failures.append(f"presets:count:{len(presets)}")
    preset_saved: dict[str, Any] | None = None
    for item in presets:
        response = client.post(
            "/v1/month/answers",
            json={"topic": item["topic"], "preset": item["id"]},
            headers=headers,
        )
        answer = _answer(response)
        if answer is None:
            failures.append(f"preset:{item['id']}:status:{response.status_code}")
            continue
        stats["preset_answers"] += 1
        if answer["preset"] != item["id"] or answer["question"] != item["text"]:
            failures.append(f"preset:{item['id']}:wrong-question")
        if not answer["tip"]:
            failures.append(f"preset:{item['id']}:no-tip")
        plain = by_topic.get(item["topic"])
        if plain is not None and any(answer[part] != plain[part] for part in MONTH_PARTS):
            failures.append(f"preset:{item['id']}:month-parts-differ")
        for part in ("tip", "theme", "act", "say"):
            if YES_NO.match(answer[part] or ""):
                failures.append(f"preset:{item['id']}:yes-no")
        if DATE_LIKE.search(response.text):
            failures.append(f"preset:{item['id']}:date-in-answer")
        if any(text in response.text for text in seen_texts):
            failures.append(f"preset:{item['id']}:other-person-text")
        if item["id"] == "mind.sleep":
            preset_saved = answer

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
    saved_ids: list[str] = []
    for topic, picked in (("work", first_work), ("mind", preset_saved)):
        if picked is None:
            continue
        response = client.post(
            "/v1/month/saved",
            json={"topic": topic, "answer_key": picked["answer_key"]},
            headers=headers,
        )
        if response.status_code != 201:
            failures.append(f"save:{response.status_code}")
            continue
        saved_ids.append(response.json()["id"])
        if response.json()["answer"]["question"] != picked["question"]:
            failures.append("save:question-mismatch")
    if saved_ids:
        saved_id = saved_ids[0]
        listed = client.get("/v1/month/saved", headers=headers).json()["items"]
        if sorted(item["id"] for item in listed) != sorted(saved_ids):
            failures.append("save:list-mismatch")

    questions = [q["text"] for q in persona.get("tarot_questions", []) if len(q["text"]) >= 8]
    tests = persona.get("tests", {})
    crisis = [i["text"] if isinstance(i, dict) else i for i in tests.get("crisis_inputs", [])]
    for text in [*questions[:1], *crisis[:1]]:
        stats["free_text_sent"] += 1
        response = client.post(
            "/v1/month/answers", json={"topic": "work", "question": text[:280]}, headers=headers
        )
        if response.status_code != 422:
            failures.append(f"free-text:accepted:{response.status_code}")
        elif text[:280] in response.text:
            failures.append("free-text:echoed")
        else:
            stats["free_text_refused"] += 1
    stats["tarot_questions"] += len(questions)
    for text in questions:
        lowered = text.lower()
        hits = [key for key, pattern in PRESET_THEMES.items() if pattern.search(lowered)]
        if hits:
            stats["tarot_questions_matching_a_preset"] += 1
        for key in hits:
            stats[f"want:{key}"] += 1
    for key, pattern in PRESET_THEMES.items():
        if any(pattern.search(text.lower()) for text in questions):
            stats[f"want_personas:{key}"] += 1

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
    asked = totals["tarot_questions"]
    summary = {
        "git_head": git_head(),
        "personas": len(rows),
        "by_precision": dict(by_precision),
        "seconds": round(time.monotonic() - started, 1),
        "database": "local SQLite per worker (synthetic, deleted with the temp dir)",
        "copy": "month.* served as approved in memory for this run only",
        "topic_answers": totals["topic_answers"],
        "preset_answers": totals["preset_answers"],
        "free_text": {
            "sent": totals["free_text_sent"],
            "refused": totals["free_text_refused"],
        },
        "persona_wants": {
            "tarot_questions": asked,
            "matching_a_preset": totals["tarot_questions_matching_a_preset"],
            "share": round(totals["tarot_questions_matching_a_preset"] / asked, 4)
            if asked
            else None,
            "personas_per_preset": {key: totals[f"want_personas:{key}"] for key in PRESET_THEMES},
            "questions_per_preset": {key: totals[f"want:{key}"] for key in PRESET_THEMES},
            "method": "rough keyword match on the lowercased Tarot question; report only",
        },
        "failures": dict(failures),
        "failing_personas": [row["persona"] for row in rows if row["failures"]],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
