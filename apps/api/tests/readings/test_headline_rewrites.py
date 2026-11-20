"""A Daily headline that says the reader is tired never lands on a "Rực" or "Chill" day (#777).

The headline is picked before the mood, so the only way to keep "Bạn đang mệt, …" off a good-mood
day is to stop serving it. Each such code headline has a rewrite pair (direct and roast) in the
copy registry; it replaces the code headline once BOTH sentences are approved.

The checks hold whatever the checked-in registry says (Codex auto-1 on #788): the end-to-end cases
run in a fresh process over an explicit fixture registry, once with the pairs pending and once
with them approved before the app modules are imported, as a Codex copy batch will leave them.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.domains.content import copy_approval
from app.domains.content.copy_approval import copy_digest, load_registry, parse_registry
from app.domains.readings import headline_rewrites
from app.domains.readings.daily_psychology import _DAILY_VARIATIONS, DAILY_ISSUES
from app.domains.readings.headline_rewrites import (
    HEADLINE_REWRITES,
    REWRITE_PREFIX,
    approved_rewrite,
    asserts_tiredness,
    rewrite_ids,
    served_headline,
)
from app.domains.readings.voice import ROAST_ISSUES, DailySections, roast_daily_sections
from tests.content.test_daily_variants import _check_clarity, _check_headline

API = Path(__file__).resolve().parents[2]
REGISTRY = load_registry()
# Made-up rewrites for the fixture registry, independent of the checked-in sentences.
FIXTURE_TEXTS = {
    old: (f"Câu thay thử số {n} cho tiêu đề này.", f"Câu khịa thử số {n} cho tiêu đề này.")
    for n, old in enumerate(sorted(HEADLINE_REWRITES), start=1)
}


def _approved(entry_id: str, text: str, category: str = "reading") -> dict[str, Any]:
    return {
        "id": entry_id,
        "category": category,
        "text": text,
        "status": "approved",
        "approver": "codex",
        "date": "2026-11-20",
        "digest": copy_digest(text),
    }


def _authored_headlines() -> set[str]:
    """Every headline written in code, whether or not its rewrite is already approved."""

    titles = {title for titles, _, _ in _DAILY_VARIATIONS.values() for title in titles}
    pairs = {direct for voice in ROAST_ISSUES.values() for direct, _ in voice.headlines}
    served = {*(h for issue in DAILY_ISSUES for h in issue.headlines), *titles, *pairs}
    replaced = {old: rw[0] for old in HEADLINE_REWRITES if (rw := approved_rewrite(old))}
    return (served - set(replaced.values())) | set(replaced)


def _fixture_registry(path: Path, *, approve: bool) -> None:
    """The checked-in registry without its rewrite entries, plus made-up rewrite pairs."""

    raw = json.loads(copy_approval.REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = [e for e in raw["entries"] if not str(e["id"]).startswith(REWRITE_PREFIX)]
    for old, (direct, roast) in FIXTURE_TEXTS.items():
        for entry_id, text in zip(
            rewrite_ids(*HEADLINE_REWRITES[old]), (direct, roast), strict=True
        ):
            entries.append(
                _approved(entry_id, text)
                if approve
                else {"id": entry_id, "category": "reading", "text": text, "status": "pending"}
            )
    path.write_text(json.dumps({**raw, "entries": entries}, ensure_ascii=False), encoding="utf-8")


# Runs in a fresh interpreter: the registry is in place before any Daily module is imported.
_PROBE = """
import json, sys
from datetime import timedelta
from pathlib import Path
from app.domains.content import copy_approval
copy_approval.REGISTRY_PATH = Path(sys.argv[1])
from app.domains.readings.daily_psychology import DAILY_ISSUES
from app.domains.readings.headline_rewrites import asserts_tiredness
from app.domains.readings.models import ReadingPurpose
from app.domains.readings.planner import ReadingPlanner
from app.domains.readings.renderers import DeterministicVietnameseRenderer
from app.domains.readings.voice import ROAST_ISSUES, DailySections, roast_daily_sections
from tests.readings.test_date_only_issue_rotation import START, _source, _variety

days = []
planner, renderer = ReadingPlanner(), DeterministicVietnameseRenderer()
for sign in ("cancer", "scorpio", "pisces"):
    for offset in range(72):
        if ("Rực", "Chill", "Đuối", "Căng")[offset % 4] not in ("Rực", "Chill"):
            continue
        day = START + timedelta(days=offset)
        plan = planner.plan(_source(sign), purpose=ReadingPurpose.DAILY_NOTE,
                            editorial_seed=day.isoformat(), daily_variety=_variety(day))
        card = renderer.render(plan)
        roast = roast_daily_sections(
            DailySections(card.hook, card.thesis, card.manifestation, card.micro_action))
        days.append([card.hook, roast.hook])
pool = sorted({h for issue in DAILY_ISSUES for h in issue.headlines})
pairs = sorted({tuple(p) for v in ROAST_ISSUES.values() for p in v.headlines})
print(json.dumps({"days": days, "pool": pool, "pairs": pairs}, ensure_ascii=False))
"""


def _probe(tmp_path: Path, *, approve: bool) -> dict[str, Any]:
    registry = tmp_path / f"registry-{'approved' if approve else 'pending'}.json"
    _fixture_registry(registry, approve=approve)
    done = subprocess.run(  # noqa: S603 - fixed argv: this interpreter and a literal script
        [sys.executable, "-c", _PROBE, str(registry)],
        cwd=API,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    result: dict[str, Any] = json.loads(done.stdout.strip().splitlines()[-1])
    return result


def test_every_code_headline_that_says_tired_has_a_rewrite_pair_in_the_registry() -> None:
    tired = {headline for headline in _authored_headlines() if asserts_tiredness(headline)}
    assert tired == set(HEADLINE_REWRITES)
    for issue, number in HEADLINE_REWRITES.values():
        assert any(issue == item.key for item in DAILY_ISSUES)
        for entry_id in rewrite_ids(issue, number):
            assert entry_id in REGISTRY, entry_id
            assert REGISTRY[entry_id].category == "reading"


@pytest.mark.parametrize("headline", sorted(HEADLINE_REWRITES))
def test_the_rewrite_names_the_habit_and_passes_the_headline_gates(headline: str) -> None:
    direct_id, roast_id = rewrite_ids(*HEADLINE_REWRITES[headline])
    direct, roast = REGISTRY[direct_id].text, REGISTRY[roast_id].text
    assert not asserts_tiredness(direct) and not asserts_tiredness(roast)
    assert direct != roast and direct != headline
    _check_clarity(direct_id, direct)
    _check_headline(direct_id, direct)
    _check_clarity(roast_id, roast)
    # A rewrite never duplicates another headline of the catalog.
    others = _authored_headlines() - {headline}
    assert direct not in others and roast not in others


def test_the_detector_reads_vietnamese_words_not_substrings() -> None:
    assert asserts_tiredness("Bạn đang mệt, vẫn nhận thêm việc.")
    assert asserts_tiredness("Pin đã đỏ mà vẫn nhận thêm việc.")
    assert not asserts_tiredness("Bạn nhận thêm việc khi lịch đã kín.")


def test_while_pending_the_tired_headline_is_still_served(tmp_path: Path) -> None:
    # The bug this fixes: with the rewrites pending, a good-mood day can still say "mệt".
    probe = _probe(tmp_path, approve=False)
    assert any(asserts_tiredness(direct) for direct, _ in probe["days"])


def test_no_tired_headline_on_a_good_mood_day_once_the_rewrites_are_approved(
    tmp_path: Path,
) -> None:
    probe = _probe(tmp_path, approve=True)
    assert [pair for pair in probe["days"] if any(asserts_tiredness(t) for t in pair)] == []
    # The pool and the Roast pairs carry the rewrite, never the replaced headline...
    assert not any(asserts_tiredness(headline) for headline in probe["pool"])
    pairs = {tuple(pair) for pair in probe["pairs"]}
    for direct, roast in FIXTURE_TEXTS.values():
        assert (direct, roast) in pairs
    # ...and a served rewrite is voiced with its own roast.
    roasts = dict(FIXTURE_TEXTS.values())
    served = [(direct, roast) for direct, roast in probe["days"] if direct in roasts]
    assert served and all(roast == roasts[direct] for direct, roast in served)


def test_a_half_approved_pair_keeps_the_code_headline(monkeypatch: pytest.MonkeyPatch) -> None:
    entries = [
        _approved(rewrite_ids(*HEADLINE_REWRITES[old])[0], direct)
        for old, (direct, _) in FIXTURE_TEXTS.items()
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)
    for headline in HEADLINE_REWRITES:
        assert approved_rewrite(headline) is None
        assert served_headline(headline) == headline


def test_a_rewrite_that_still_says_tired_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    headline = next(iter(HEADLINE_REWRITES))
    direct_id, roast_id = rewrite_ids(*HEADLINE_REWRITES[headline])
    entries = [
        _approved(direct_id, "Bạn đã mệt mà vẫn giúp."),
        _approved(roast_id, "Một câu khác."),
    ]
    registry = parse_registry({"version": copy_approval.REGISTRY_VERSION, "entries": entries})
    monkeypatch.setattr(copy_approval, "_runtime_registry", lambda: registry)
    assert headline_rewrites.served_headline(headline) == headline


def test_a_saved_note_with_the_old_headline_keeps_its_old_roast() -> None:
    old = "Bạn đang mệt, vẫn nhận thêm việc giúp người khác."
    issue = next(item for item in DAILY_ISSUES if item.key == "automatic-caretaking")
    roast = roast_daily_sections(
        DailySections(old, f"x {issue.takeaway}", issue.scenes[0], issue.advice[0])
    )
    assert roast.hook == "Pin đã đỏ mà vẫn nhận thêm việc giúp người khác."
