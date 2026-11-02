"""The release review's clarity ratchet: coverage (spec A12), baseline file and CLI flag."""

import json
from pathlib import Path

import pytest

from app.domains.readings.clarity_lint import RULES, SurfaceReport, ratchet_regressions
from scripts import review_content_release
from scripts.content_clarity_corpus import MINIMUM_SAMPLES, build_clarity_corpus
from scripts.review_content_release import BASELINE_PATH, clarity_reports


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


def test_corpus_is_deterministic(reports: dict[str, SurfaceReport]) -> None:
    assert clarity_reports() == reports


def test_committed_baseline_matches_the_rules_and_holds(
    reports: dict[str, SurfaceReport],
) -> None:
    baseline = json.loads(BASELINE_PATH.read_text("utf-8"))

    assert set(baseline["surfaces"]) == set(MINIMUM_SAMPLES)
    for surface, entry in baseline["surfaces"].items():
        assert set(entry["rules"]) == set(RULES)
        assert entry["samples"] >= MINIMUM_SAMPLES[surface]
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
    assert "A9" in output  # out-of-scope rules are listed as TODO


def test_cli_accepts_update_baseline_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reports: dict[str, SurfaceReport]
) -> None:
    path = tmp_path / "baseline.json"
    monkeypatch.setattr(review_content_release, "clarity_reports", lambda: reports)

    review_content_release.main(["--update-baseline", "--baseline", str(path)])

    assert json.loads(path.read_text("utf-8"))["surfaces"]["radar"]["samples"] == (
        reports["radar"].samples
    )
