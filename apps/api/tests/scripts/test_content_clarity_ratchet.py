"""The release review's clarity ratchet: coverage (spec A12), baseline file, base branch,
exceptions file and CLI flags."""

import json
from pathlib import Path
from typing import Any

import pytest

from app.domains.readings.clarity_lint import RULES, SurfaceReport, ratchet_regressions
from scripts import review_content_release
from scripts.content_clarity_corpus import MINIMUM_SAMPLES, build_clarity_corpus
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


def test_committed_exceptions_file_is_empty() -> None:
    assert json.loads(EXCEPTIONS_PATH.read_text("utf-8"))["exceptions"] == []


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
    path = tmp_path / "exceptions.json"
    path.write_text(json.dumps({"exceptions": list(entries)}), "utf-8")
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

    approved = _exceptions(
        tmp_path,
        {"rule": "A8", "surface": "tarot", "reason": "approved rise", "approver": "owner"},
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
    removed = base["surfaces"]["daily"]["keys"]["A14"].pop()
    head = _setup_base(tmp_path, monkeypatch, reports, base)
    capsys.readouterr()

    with pytest.raises(SystemExit):
        review_content_release._clarity_ratchet(
            head, update=False, base_ref="origin/base", exceptions_path=_exceptions(tmp_path)
        )
    output = capsys.readouterr().out
    assert (
        f"daily: A14 khẳng định việc đã xảy ra: 1 new violating sentence(s) not in the "
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
