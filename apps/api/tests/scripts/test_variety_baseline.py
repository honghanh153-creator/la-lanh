from __future__ import annotations

from collections import Counter
from typing import Any

from scripts.variety_baseline import (
    identical_pair_rate,
    min_repeat_gap,
    normalize,
    pool_bucket,
    rotation_report,
)
from scripts.variety_fixtures import OUT, build, render


def test_normalize_folds_case_space_and_trailing_punctuation() -> None:
    assert normalize("  Hỏi lại   một câu thôi. ") == "hỏi lại một câu thôi"
    assert normalize("Đọc hết đã nha!") == normalize("đọc hết đã nha")


def test_min_repeat_gap_ignores_missing_days() -> None:
    assert min_repeat_gap(["a", "b", "a", None, "a"]) == 2
    assert min_repeat_gap(["a", "b", "c"]) is None
    assert min_repeat_gap([None, None]) is None


def test_identical_pair_rate_counts_pairs_within_groups() -> None:
    same, total = identical_pair_rate([Counter({"x": 3, "y": 1}), Counter({"z": 2})])
    assert (same, total) == (3 + 1, 6 + 1)


def test_pool_bucket_edges() -> None:
    assert [pool_bucket(n) for n in (0, 1, 2, 3, 4)] == ["1", "1", "2-3", "2-3", ">=4"]


def test_committed_fixtures_match_the_generator() -> None:
    for name, doc in build().items():
        assert (OUT / name).read_text() == render(doc), (
            f"{name} drifted; rerun scripts.variety_fixtures"
        )


def test_pool_stratum_uses_the_daily_pool_not_the_winners() -> None:
    from scripts.variety_baseline import pool_stratum

    # Six different issues may win over a window, but the daily pool was 1 or 2.
    assert pool_stratum([1] * 139 + [2] * 61) == "1"
    assert pool_stratum([2, 3, 2, 1]) == "2-3"
    assert pool_stratum([5, 4, 6, 4]) == ">=4"
    assert pool_stratum([1, 1, 4, 4]) == "1"  # ties go to the smaller bucket


def test_personal_sources_counts_independent_sources_once() -> None:
    from scripts.variety_baseline import personal_sources

    # Transit supports a natal pair resting on a house: transit + natal configuration.
    assert personal_sources(True, ["natal_aspect", "planet_placement", "house_placement"]) == 2
    # No transit, a placement rule refined by a house: natal configuration only.
    assert personal_sources(False, ["planet_placement", "house_placement"]) == 1
    # Transit drives a situation on a single placement: transit only.
    assert personal_sources(True, ["transit_contact", "planet_placement"]) == 1
    # A single sign placement is not a personal configuration; pair + house count once.
    assert personal_sources(False, ["planet_placement"]) == 0
    assert personal_sources(False, ["natal_aspect", "house_placement"]) == 1


def test_radar_visible_text_includes_nested_blocks_and_scopes_sections() -> None:
    from scripts.variety_baseline import changed_share, radar_sentences

    reading: dict[str, Any] = {
        "headline": "Tiêu đề.",
        "summary": "Tóm tắt.",
        "pair_signature": {"headline": "Chữ ký.", "summary": "Chữ ký tóm tắt."},
        "compatibility_map": [{"meaning": "Ý nghĩa bản đồ."}],
        "sections": [
            {
                "key": "fit",
                "title": "Hợp.",
                "body": "Thân hợp.",
                "highlights": [{"title": "Điểm sáng.", "body": "Thân điểm sáng."}],
                "scene": {"title": "Cảnh.", "body": "zqcanary cảnh hợp."},
                "perspectives": [{"title": "Phía bạn.", "body": "Góc nhìn."}],
                "observation": {"title": "Quan sát.", "body": "Thân quan sát."},
            },
            {"key": "check", "title": "Kiểm.", "body": "Thân kiểm."},
        ],
    }
    everything = radar_sentences(reading)
    assert "zqcanary cảnh hợp" in everything and "góc nhìn" in everything
    assert "ý nghĩa bản đồ" in everything and "chữ ký tóm tắt" in everything
    scoped = radar_sentences(reading, ("fit", "friction"))
    assert "thân kiểm" not in scoped and "tiêu đề" not in scoped
    changed = {**reading, "sections": [{**reading["sections"][0], "scene": {"body": "Khác."}}]}
    assert changed_share(scoped, radar_sentences(changed, ("fit", "friction"))) > 0


def test_tarot_matrix_covers_every_map_and_pairs_are_counted() -> None:
    from app.domains.tarot.engine import TarotReadingEngine
    from app.domains.tarot.models import TarotSpreadMap
    from scripts.variety_baseline import different_pairs, duplicate_rate, tarot_matrix

    assert {m for m, _, _ in tarot_matrix(TarotReadingEngine())} == set(TarotSpreadMap)
    assert different_pairs({"q1": "a", "q2": "a", "q3": "b"}) == (2, 3)
    assert duplicate_rate(["x", "x", "y", "z"]) == 0.25


def test_tarot_report_measures_every_voice() -> None:
    import inspect

    from scripts import variety_baseline

    source = inspect.getsource(variety_baseline.tarot_report)
    assert "voices = list(TarotVoice)" in source
    assert "headlines[voice.value]" in source  # T2 aggregates by voice, not by map


def _n(issue: str, h: str, s: str, a: str, pool: int = 2) -> dict[str, Any]:
    return {"issue": issue, "headline": h, "scene": s, "advice": a, "pool": pool}


def test_rotation_report_counts_axis_repeats_runs_and_combo_reuse() -> None:
    series = [
        _n("x", "h1", "s1", "a1"),
        _n("x", "h1", "s2", "a2"),  # same situation, headline repeated
        _n("x", "h2", "s3", "a3"),  # third day in a row with a pool of two
        _n("y", "h1", "s1", "a1"),
        _n("x", "h1", "s1", "a1", pool=1),  # full combo seen 4 days earlier
    ]
    report = rotation_report([{"id": "p"}], {"p": series})

    assert report["consecutive_pairs"] == 4
    assert report["same_situation_consecutive_pairs"] == 2
    assert report["same_situation_axis_repeats"] == {"headline": 1, "scene": 0, "advice": 0}
    assert report["three_day_same_situation_runs_with_pool_ge_2"] == 1
    assert report["full_combo_seen_in_previous_30d_rate"] == round(2 / 5, 4)
