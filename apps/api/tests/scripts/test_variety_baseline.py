from __future__ import annotations

from collections import Counter

from scripts.variety_baseline import identical_pair_rate, min_repeat_gap, normalize, pool_bucket
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
