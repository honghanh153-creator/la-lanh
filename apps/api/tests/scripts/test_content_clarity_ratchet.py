"""The release review's clarity ratchet: coverage (spec A12), baseline file, base branch,
exceptions file and CLI flags."""

import copy
import json
import re
from pathlib import Path
from typing import Any, get_args

import pytest
from pydantic import BaseModel

from app.domains.astro.models import NatalChart
from app.domains.readings.clarity_lint import (
    HARD_ZERO_RULES,
    RULES,
    ClarityDocument,
    SurfaceReport,
    hard_zero_violations,
    keys_digest,
    lint_document,
    ratchet_regressions,
)
from app.domains.tarot.models import (
    TarotReading,
    TarotReadingPosition,
    TarotStance,
    TarotStanceReason,
)
from scripts import review_content_release
from scripts.content_clarity_corpus import (
    MINIMUM_SAMPLES,
    RADAR_ITEM_LINTED_FIELDS,
    RADAR_ITEM_UNLINTED_FIELDS,
    RADAR_SECTION_LINTED_FIELDS,
    RADAR_SECTION_UNLINTED_FIELDS,
    TAROT_LINTED_FIELDS,
    TAROT_UNLINTED_FIELDS,
    build_clarity_corpus,
    daily_charts,
    daily_days,
    radar_readings,
    radar_sections,
    tarot_readings,
    tarot_sections,
)
from scripts.review_content_release import (
    BASELINE_PATH,
    EXCEPTIONS_PATH,
    clarity_reports,
    read_base_baseline,
)


@pytest.fixture(scope="module")
def reports() -> dict[str, SurfaceReport]:
    return clarity_reports()


def test_corpus_covers_every_surface_in_production_voices() -> None:
    corpus = build_clarity_corpus()

    assert {surface: len(docs) >= MINIMUM_SAMPLES[surface] for surface, docs in corpus.items()} == {
        "daily": True,
        "tarot": True,
        "radar": True,
        "kham_pha": True,
    }
    tarot = corpus["tarot"]
    assert {doc.variant for doc in tarot} == {"playful_grounded", "roast"}
    assert {
        sum(1 for section, _ in doc.sections if section.startswith("meaning_")) for doc in tarot
    } == {1, 3, 5}
    assert {doc.variant for doc in corpus["radar"]} == {"crush", "friend", "partner", "someone"}
    assert {doc.variant for doc in corpus["kham_pha"]} == {"western", "jyotish"}
    assert {doc.variant for doc in corpus["daily"]} == {"direct", "roast"}
    assert len({doc.sample_id for docs in corpus.values() for doc in docs}) == sum(
        len(docs) for docs in corpus.values()
    )


TAROT_PAGE = Path(__file__).parents[3] / "web/src/features/tarot/TarotPage.tsx"
# The names TarotPage.tsx binds each reading model to.
_TAROT_PAGE_NAMES: dict[str, type[BaseModel]] = {
    "reading": TarotReading,
    "reading.stance": TarotStance,
    "position": TarotReadingPosition,
    "reason": TarotStanceReason,
}


def _text_fields(model: type[BaseModel]) -> set[str]:
    return {
        name
        for name, info in model.model_fields.items()
        if str in (get_args(info.annotation) or (info.annotation,))
    }


def test_tarot_corpus_names_every_text_field_of_a_reading() -> None:
    models = {model.__name__: model for model in _TAROT_PAGE_NAMES.values()}

    assert set(TAROT_LINTED_FIELDS) | set(TAROT_UNLINTED_FIELDS) == set(models)
    for name, model in models.items():
        linted = TAROT_LINTED_FIELDS.get(name, frozenset())
        unlinted = TAROT_UNLINTED_FIELDS.get(name, {})
        assert not linted & set(unlinted), name
        assert linted | set(unlinted) == _text_fields(model), name
        assert all(reason.strip() for reason in unlinted.values()), name


def test_tarot_corpus_lints_every_text_field_the_page_shows() -> None:
    source = TAROT_PAGE.read_text("utf-8")
    shown: dict[str, set[str]] = {}
    for prefix, model in _TAROT_PAGE_NAMES.items():
        pattern = rf"(?<![\w.]){re.escape(prefix)}\.([a-z_]+)\b"
        fields = set(re.findall(pattern, source)) & _text_fields(model)
        shown.setdefault(model.__name__, set()).update(fields)

    assert "text" in shown["TarotStanceReason"]  # the parse still sees the reasons list
    assert "conclusion" in shown["TarotStance"]
    for name, fields in shown.items():
        unlinted = set(TAROT_UNLINTED_FIELDS.get(name, {}))
        assert fields - unlinted <= TAROT_LINTED_FIELDS[name], name


def test_a_placeholder_in_any_linted_tarot_field_is_caught() -> None:
    reading = next(
        reading
        for _, reading in tarot_readings()
        if reading.stance is not None
        and reading.stance.reasons
        and any(position.small_action for position in reading.positions)
    )
    assert reading.stance is not None

    def flagged(changed: TarotReading) -> int:
        document = ClarityDocument("tarot", "probe", tarot_sections(changed))
        return (
            lint_document(document)["A11"]
            - lint_document(ClarityDocument("tarot", "probe", tarot_sections(reading)))["A11"]
        )

    stance, reason, position = reading.stance, reading.stance.reasons[0], reading.positions[0]
    probes: dict[str, TarotReading] = {
        **{
            f"TarotReading.{field}": reading.model_copy(update={field: "TODO viết lại."})
            for field in TAROT_LINTED_FIELDS["TarotReading"]
        },
        **{
            f"TarotStance.{field}": reading.model_copy(
                update={"stance": stance.model_copy(update={field: "TODO viết lại."})}
            )
            for field in TAROT_LINTED_FIELDS["TarotStance"]
        },
        **{
            f"TarotStanceReason.{field}": reading.model_copy(
                update={
                    "stance": stance.model_copy(
                        update={
                            "reasons": (
                                reason.model_copy(update={field: "TODO viết lại."}),
                                *stance.reasons[1:],
                            )
                        }
                    )
                }
            )
            for field in TAROT_LINTED_FIELDS["TarotStanceReason"]
        },
        **{
            f"TarotReadingPosition.{field}": reading.model_copy(
                update={
                    "positions": (
                        position.model_copy(update={field: "TODO viết lại."}),
                        *reading.positions[1:],
                    )
                }
            )
            for field in TAROT_LINTED_FIELDS["TarotReadingPosition"]
        },
    }

    assert {name: flagged(changed) for name, changed in probes.items()} == dict.fromkeys(probes, 1)


RADAR_PAGE = Path(__file__).parents[3] / "web/src/features/radar/RadarContinuePage.tsx"
# The names RadarContinuePage.tsx binds the items inside a Radar section to.
_RADAR_ITEM_PAGE_NAMES = ("highlight", "perspective", "section.scene", "section.observation")
_RADAR_ITEM_LISTS = ("highlights", "perspectives")
_RADAR_ITEM_OBJECTS = ("scene", "observation")


def _page_fields(source: str, prefix: str) -> set[str]:
    return set(re.findall(rf"(?<![\w.]){re.escape(prefix)}\.([a-z_]+)\b", source))


def test_radar_corpus_names_every_section_field_the_page_shows() -> None:
    source = RADAR_PAGE.read_text("utf-8")
    section_names = RADAR_SECTION_LINTED_FIELDS | set(RADAR_SECTION_UNLINTED_FIELDS)
    item_names = RADAR_ITEM_LINTED_FIELDS | set(RADAR_ITEM_UNLINTED_FIELDS)
    shown_sections = _page_fields(source, "section")
    shown_items = set().union(*(_page_fields(source, name) for name in _RADAR_ITEM_PAGE_NAMES))

    assert {"title", "body", "question", "scene"} <= shown_sections  # the parse sees the page
    assert {"title", "body"} <= shown_items
    assert shown_sections <= section_names
    assert shown_items <= item_names
    assert not RADAR_SECTION_LINTED_FIELDS & set(RADAR_SECTION_UNLINTED_FIELDS)
    assert not RADAR_ITEM_LINTED_FIELDS & set(RADAR_ITEM_UNLINTED_FIELDS)
    assert all(reason.strip() for reason in RADAR_SECTION_UNLINTED_FIELDS.values())
    assert all(reason.strip() for reason in RADAR_ITEM_UNLINTED_FIELDS.values())


def test_radar_corpus_names_every_field_a_rendered_section_carries() -> None:
    section_keys: set[str] = set()
    item_keys: set[str] = set()
    for _, _, reading in radar_readings():
        for section in reading["sections"]:
            section_keys |= set(section)
            for name in _RADAR_ITEM_LISTS:
                for item in section.get(name) or ():
                    item_keys |= set(item)
            for name in _RADAR_ITEM_OBJECTS:
                if isinstance(section.get(name), dict):
                    item_keys |= set(section[name])

    assert section_keys <= RADAR_SECTION_LINTED_FIELDS | set(RADAR_SECTION_UNLINTED_FIELDS)
    assert item_keys <= RADAR_ITEM_LINTED_FIELDS | set(RADAR_ITEM_UNLINTED_FIELDS)


def test_a_placeholder_in_any_linted_radar_field_is_caught() -> None:
    reading = next(
        reading
        for _, _, reading in radar_readings()
        if any(section.get("question") for section in reading["sections"])
        and any(section.get("highlights") for section in reading["sections"])
        and any(section.get("perspectives") for section in reading["sections"])
    )
    probe = "TODO viết lại."

    def flagged(changed: dict[str, Any]) -> int:
        def a11(result: dict[str, Any]) -> int:
            return lint_document(ClarityDocument("radar", "probe", radar_sections(result)))["A11"]

        return a11(changed) - a11(reading)

    def edit(index: int, change: Any) -> dict[str, Any]:
        changed = copy.deepcopy(reading)
        change(changed["sections"][index])
        return changed

    probes: dict[str, dict[str, Any]] = {}
    for index, section in enumerate(reading["sections"]):
        key = section["key"]
        for field in ("title", "body", "question"):
            if field in section:
                probes[f"{key}.{field}"] = edit(index, lambda s, f=field: s.update({f: probe}))
        for name in _RADAR_ITEM_LISTS:
            if section.get(name):
                for field in sorted(RADAR_ITEM_LINTED_FIELDS):
                    probes[f"{key}.{name}[0].{field}"] = edit(
                        index, lambda s, n=name, f=field: s[n][0].update({f: probe})
                    )
        for name in _RADAR_ITEM_OBJECTS:
            for field in sorted(RADAR_ITEM_LINTED_FIELDS):
                item = {"key": "probe", "label": "Nhãn", "title": "Một dòng.", "body": "Một dòng."}
                probes[f"{key}.{name}.{field}"] = edit(
                    index, lambda s, n=name, i=item, f=field: s.update({n: {**i, f: probe}})
                )
        probes[f"{key}.observation(text)"] = edit(index, lambda s: s.update(observation=probe))

    assert {"fit.title", "check.question", "why.title"} <= set(probes)
    assert {name: flagged(changed) for name, changed in probes.items()} == dict.fromkeys(probes, 1)


def test_corpus_is_deterministic(reports: dict[str, SurfaceReport]) -> None:
    assert clarity_reports() == reports


def test_committed_baseline_matches_the_rules_and_holds(
    reports: dict[str, SurfaceReport],
) -> None:
    baseline = json.loads(BASELINE_PATH.read_text("utf-8"))

    assert set(baseline["surfaces"]) == set(MINIMUM_SAMPLES)
    for surface, entry in baseline["surfaces"].items():
        assert set(entry["rules"]) == set(RULES)
        assert set(entry["keys"]) == set(RULES)
        assert entry["samples"] >= MINIMUM_SAMPLES[surface]
        for keys in entry["keys"].values():
            assert all(len(key) == 10 and int(key, 16) >= 0 for key in keys)  # hashes only
    assert ratchet_regressions(reports, baseline, minimum_samples=MINIMUM_SAMPLES) == ()


def test_update_baseline_flag_rewrites_then_ratchet_blocks_a_rise(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    path = tmp_path / "baseline.json"
    monkeypatch.setattr(review_content_release, "clarity_reports", lambda: reports)

    review_content_release._clarity_ratchet(path, update=True)
    review_content_release._clarity_ratchet(path, update=False)
    assert "Clarity ratchet passed" in capsys.readouterr().out

    baseline = json.loads(path.read_text("utf-8"))
    baseline["surfaces"]["tarot"]["rules"]["A8"] -= 1
    path.write_text(json.dumps(baseline), "utf-8")
    with pytest.raises(SystemExit) as exit_info:
        review_content_release._clarity_ratchet(path, update=False)
    assert exit_info.value.code == 1
    output = capsys.readouterr().out
    assert "tarot: A8 câu > 25 âm tiết rose to" in output
    assert "A1+" in output  # rules not measured yet are listed as TODO


def test_cli_accepts_update_baseline_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reports: dict[str, SurfaceReport]
) -> None:
    path = tmp_path / "baseline.json"
    monkeypatch.setattr(review_content_release, "clarity_reports", lambda: reports)

    review_content_release.main(["--update-baseline", "--baseline", str(path)])

    assert json.loads(path.read_text("utf-8"))["surfaces"]["radar"]["samples"] == (
        reports["radar"].samples
    )


def test_committed_exceptions_only_list_pre_existing_hard_zero_sentences(
    reports: dict[str, SurfaceReport],
) -> None:
    all_entries = json.loads(EXCEPTIONS_PATH.read_text("utf-8"))["exceptions"]
    entries = [entry for entry in all_entries if entry["rule"] in HARD_ZERO_RULES]
    # Ratchet waivers are allowed only with a named owner approval and a reason.
    waivers = [entry for entry in all_entries if entry["rule"] not in HARD_ZERO_RULES]
    assert all(
        entry["approver"].startswith("owner") and entry["reason"] and "keys" not in entry
        for entry in waivers
    )
    # Each waiver is bound to the approved count and key set (Codex P1 on #219).
    assert all(
        isinstance(entry["max_count"], int) and len(entry["keys_digest"]) == 64 for entry in waivers
    )
    assert all(entry["reason"].startswith("pre-existing") and entry["keys"] for entry in entries)
    # Every listed key is still present; drop an entry as soon as C3 fixes the sentence.
    for entry in entries:
        assert set(entry["keys"]) <= set(reports[entry["surface"]].keys[entry["rule"]])
    assert hard_zero_violations(reports) != ()  # the gate does see the pre-existing hits


def _setup_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reports: dict[str, SurfaceReport],
    base: dict[str, Any] | None,
    status: str = "found",
) -> Path:
    head = tmp_path / "baseline.json"
    monkeypatch.setattr(review_content_release, "clarity_reports", lambda: reports)
    monkeypatch.setattr(review_content_release, "read_base_baseline", lambda ref: (base, status))
    review_content_release._clarity_ratchet(head, update=True, base_ref=None)
    return head


def _exceptions(tmp_path: Path, *entries: dict[str, str]) -> Path:
    """The committed exceptions plus ``entries``."""
    committed = json.loads(EXCEPTIONS_PATH.read_text("utf-8"))["exceptions"]
    path = tmp_path / "exceptions.json"
    path.write_text(json.dumps({"exceptions": [*committed, *entries]}), "utf-8")
    return path


def test_a_pr_raising_its_own_baseline_fails_against_the_base_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    base = json.loads(BASELINE_PATH.read_text("utf-8"))
    base["surfaces"]["tarot"]["rules"]["A8"] -= 1  # the base branch had one long sentence less
    head = _setup_base(tmp_path, monkeypatch, reports, base)
    capsys.readouterr()

    with pytest.raises(SystemExit):
        review_content_release._clarity_ratchet(
            head, update=False, base_ref="origin/base", exceptions_path=_exceptions(tmp_path)
        )
    output = capsys.readouterr().out
    assert "compares with the baseline on origin/base" in output
    assert "tarot: baseline file raises A8 from" in output
    assert "tarot: A8 câu > 25 âm tiết rose to" in output

    tarot = json.loads(head.read_text("utf-8"))["surfaces"]["tarot"]
    approved = _exceptions(
        tmp_path,
        {
            "rule": "A8",
            "surface": "tarot",
            "reason": "approved rise",
            "approver": "owner",
            "max_count": tarot["rules"]["A8"],
            "keys_digest": keys_digest(tarot["keys"]["A8"]),
        },
    )
    review_content_release._clarity_ratchet(
        head, update=False, base_ref="origin/base", exceptions_path=approved
    )
    assert "Clarity ratchet passed" in capsys.readouterr().out


def test_a_new_violation_key_fails_even_when_counts_hold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    base = json.loads(BASELINE_PATH.read_text("utf-8"))
    removed = base["surfaces"]["daily"]["keys"]["A8"].pop()
    head = _setup_base(tmp_path, monkeypatch, reports, base)
    capsys.readouterr()

    with pytest.raises(SystemExit):
        review_content_release._clarity_ratchet(
            head, update=False, base_ref="origin/base", exceptions_path=_exceptions(tmp_path)
        )
    output = capsys.readouterr().out
    assert (
        f"daily: A8 câu > 25 âm tiết: 1 new violating sentence(s) not in the "
        f"baseline ({removed})" in output
    )
    assert "rose to" not in output


def test_missing_base_baseline_falls_back_to_the_working_copy_with_a_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    head = _setup_base(tmp_path, monkeypatch, reports, None, status="missing")
    capsys.readouterr()

    review_content_release._clarity_ratchet(head, update=False, base_ref="origin/base")
    output = capsys.readouterr().out
    assert "Warning: origin/base has no baseline yet" in output
    assert "Clarity ratchet passed" in output


def test_github_actions_fails_when_the_base_ref_cannot_be_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    head = _setup_base(tmp_path, monkeypatch, reports, None, status="no-ref")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    capsys.readouterr()

    with pytest.raises(SystemExit):
        review_content_release._clarity_ratchet(head, update=False, base_ref="origin/base")
    assert "origin/base: base ref not available" in capsys.readouterr().out


def test_read_base_baseline_reads_a_git_ref() -> None:
    assert read_base_baseline("refs/heads/no-such-branch-for-the-ratchet") == (None, "no-ref")
    assert read_base_baseline("--output=/tmp/x") == (None, "no-ref")
    document, status = read_base_baseline("HEAD")
    assert status in {"found", "missing"}
    assert (document is not None) == (status == "found")


def test_a_hard_zero_hit_fails_even_after_rewriting_the_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    tarot = reports["tarot"]
    harmful = SurfaceReport(
        surface="tarot",
        samples=tarot.samples,
        variants=tarot.variants,
        rules=tarot.rules,
        readings_flagged=tarot.readings_flagged,
        keys={**tarot.keys, "S5": ("0123456789",)},
        hard_zero={**tarot.hard_zero, "S5": 1},
    )
    head = _setup_base(tmp_path, monkeypatch, {**reports, "tarot": harmful}, None, "missing")
    capsys.readouterr()

    with pytest.raises(SystemExit):
        review_content_release._clarity_ratchet(head, update=False, base_ref=None)
    assert "tarot: S5 chắc chắn, định mệnh is a hard zero: 1 sentence(s) (0123456789)" in (
        capsys.readouterr().out
    )


def test_every_reading_declares_its_first_screen_and_facts() -> None:
    corpus = build_clarity_corpus()
    for surface, documents in corpus.items():
        for document in documents:
            names = {name for name, _ in document.sections}
            assert document.first_screen_limit is not None, document.sample_id
            assert set(document.first_screen) & names, document.sample_id
            # A15 runs wherever a chart stands behind the text; Tarot has none.
            assert (document.facts is None) == (surface == "tarot"), document.sample_id
    assert {doc.first_screen_limit for doc in corpus["tarot"]} == {120, 250, 400}


def test_a13_reads_thirty_days_for_every_persona_with_a_birth_time() -> None:
    days = daily_days()
    personas = {day.persona for day in days}
    exact = sum(isinstance(chart, NatalChart) for chart in daily_charts())
    assert len(personas) == exact == 32
    assert len(days) == 30 * exact


def test_clarity_reports_include_a13_for_daily(reports: dict[str, SurfaceReport]) -> None:
    assert reports["daily"].keys["A13"]  # Daily v1 does not follow the day yet (C2a/C4)
    assert all(not reports[surface].keys["A13"] for surface in ("tarot", "radar", "kham_pha"))


def test_pending_exceptions_are_announced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    reports: dict[str, SurfaceReport],
) -> None:
    head = _setup_base(tmp_path, monkeypatch, reports, None, "missing")
    capsys.readouterr()
    review_content_release._clarity_ratchet(head, update=False, base_ref=None)
    output = capsys.readouterr().out
    entries = json.loads(EXCEPTIONS_PATH.read_text("utf-8"))["exceptions"]
    pending = [entry for entry in entries if entry["approver"].casefold().startswith("pending")]
    assert ("Awaiting owner approval" in output) == bool(pending)
