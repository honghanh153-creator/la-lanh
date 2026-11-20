import json
from pathlib import Path
from typing import Any

from scripts.persona_metrics import (
    BENCHMARK_D7,
    BENCHMARK_D28,
    DayExperience,
    calibrate,
    contradicts_mood,
    crisis_routed,
    distinct_in_windows,
    is_light,
    light_by_rule,
    population_curve,
    repeats_ever,
    repeats_within,
    signals,
)
from scripts.persona_validate import problems

PERSONAS = Path(__file__).resolve().parents[4] / "qa" / "personas" / "personas-100.json"


def _personas() -> list[dict[str, object]]:
    data: list[dict[str, object]] = json.loads(PERSONAS.read_text(encoding="utf-8"))["personas"]
    return data


def test_the_committed_personas_meet_the_mix_and_safety_quotas() -> None:
    assert problems(json.loads(PERSONAS.read_text(encoding="utf-8"))) == []


def test_light_rule_separates_rest_from_social_or_work_steps() -> None:
    assert light_by_rule("Uống một ngụm nước rồi thở chậm ba lần.")
    assert light_by_rule("Gạch bớt một việc chưa cần làm hôm nay.")
    assert not light_by_rule("Nói rõ bạn cần bao nhiêu thời gian để làm phần được nhờ.")
    assert not light_by_rule("Đặt 20 phút cho một việc. Hết giờ mới xem việc tiếp theo.")
    assert not light_by_rule(None)


def test_explicit_weight_then_blind_label_then_rule() -> None:
    labels = {"nói rõ một việc": "light"}
    assert is_light("Nói rõ một việc.", labels, "heavy") == (False, "api")
    assert is_light("Nói rõ một việc.", labels) == (True, "label")
    assert is_light("Uống nước", {}) == (True, "rule")


def test_mood_contradiction_only_flags_statements_about_the_person() -> None:
    assert contradicts_mood("Bạn đang mệt, nghỉ chút nhé.", "Chill")
    assert contradicts_mood("Bạn đang nhiều năng lượng.", "Đuối")
    assert contradicts_mood("Hôm nay thử sức một việc khó hơn.", "Đuối")
    assert not contradicts_mood("Hỏi lại một câu thôi, đỡ hơn đoán cả buổi.", "Đuối")
    assert not contradicts_mood("Bạn đang mệt, nghỉ chút nhé.", "Đuối")


def test_crisis_detector_needs_a_support_route_not_just_a_refusal() -> None:
    normal = {"id": "x", "reading": {"headline": "Lúc này, điều đáng nhìn rõ.", "summary": "..."}}
    assert not crisis_routed(201, normal)
    assert not crisis_routed(422, {"code": "TAROT_QUESTION_REJECTED"})
    assert crisis_routed(200, {"crisis_support": {"lines": ["..."]}})
    assert crisis_routed(422, {"code": "CRISIS_SUPPORT_REQUIRED"})
    assert crisis_routed(200, {"message": "Gọi đường dây nóng hỗ trợ ngay nhé."})


def test_return_path_and_memory_signals() -> None:
    assert signals({"follow_up": {"action": "x"}}, "") == (True, True)
    assert signals({"tomorrow_preview": "x"}, "") == (True, False)
    assert signals({}, "Hôm qua bạn đã giữ việc nhỏ.") == (False, True)
    assert signals({"follow_up": None}, "") == (False, False)


def test_repetition_helpers() -> None:
    assert repeats_within(["a", "b", "a", "c", "c"], 7) == 2
    assert repeats_within(["a", "b", "c", "d", "e", "f", "g", "a"], 7) == 0
    assert repeats_ever(["a", "b", "a", None, "b"]) == 2
    assert distinct_in_windows(["z", *"abcdefghijklmn", *"aaaaaaaaaaaaaa"]) == [14, 1]


def test_return_model_is_calibrated_and_moves_the_right_way() -> None:
    personas = _personas()
    k_h, alpha = calibrate(personas)
    n = len(personas)

    def curve(exp: DayExperience) -> list[float]:
        return population_curve(personas, {str(p["id"]): [exp] * 29 for p in personas}, k_h, alpha)

    ref = curve(DayExperience())
    assert abs(ref[7] - BENCHMARK_D7) < 0.002 and abs(ref[28] - BENCHMARK_D28) < 0.002, n
    better = curve(DayExperience(understood=4.0, return_path=True, memory=True))
    worse = curve(DayExperience(understood=2.0, repeated=True, mood_miss=True))
    assert better[7] > ref[7] > worse[7]
    assert better[28] > ref[28] > worse[28]


def test_merged_plan_packets_use_plain_moods_and_reproduce_baseline() -> None:
    from scripts.persona_plan import MOOD_VI, baseline_understood, mood_today
    from scripts.persona_top8 import personas

    people = personas()
    assert {m for p in people for m in p["mood_29"]} <= set(MOOD_VI)
    assert mood_today(people[0], "tired", "A") == "Mệt"
    base = baseline_understood()
    assert len(base) == 100
    assert round(sum(base.values()) / len(base), 2) == 2.23
    assert sum(1 for v in base.values() if v >= 3) == 11


def test_merged_plan_game_checks_not_applicable_for_non_players() -> None:
    from scripts.persona_plan import drop_not_played, share

    rows: list[dict[str, Any]] = [
        {"persona": "P1", "moment": "B", "checks": {"game_understood": False, "game_hurt": False}},
        {"persona": "P2", "moment": "B", "checks": {"game_understood": True}},
        {"persona": "P3", "moment": "B", "checks": {"game_understood": None}},
        {"persona": "P1", "moment": "A", "checks": {"found_right_path": True}},
    ]
    assert drop_not_played(rows, {"P1": False, "P2": True}) == 1
    assert "game_understood" not in rows[0]["checks"]
    assert rows[0]["checks"]["game_hurt"] is False
    assert share(rows, "game_understood", True) == (1, 1)


# Issue #689: is the measurement itself stable? Synthetic scores only.
def _score(pid: str, value: int = 3, **changes: Any) -> dict[str, Any]:
    from scripts.persona_stability import FLAGS, SCORES

    return {
        "persona": pid,
        **dict.fromkeys(SCORES, value),
        **dict.fromkeys(FLAGS, False),
        **changes,
    }


def _passes(
    n: int, changes: dict[int, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    from scripts.persona_stability import parse_scores

    ids = [f"P{i:03d}" for i in range(1, n + 1)]
    first = parse_scores([_score(pid) for pid in ids])
    again = parse_scores([_score(pid, **changes.get(i, {})) for i, pid in enumerate(ids)])
    return first, again, ids


def _marks(first: Any, again: Any, ids: list[str]) -> list[bool]:
    from scripts.persona_stability import compare, stability_checks

    return [ok for _, _, ok in stability_checks(compare(first, again, ids))]


def test_stability_passes_when_a_rescoring_stays_inside_every_mark() -> None:
    # 10 of 100 personas move by 2 on one score, 5 up and 5 down: exactly at the 10% mark.
    moved = {i: {"peaceful": 5 if i % 2 else 1} for i in range(10)}
    assert _marks(*_passes(100, moved)) == [True, True, True, True]


def test_stability_fails_on_each_mark_alone() -> None:
    from scripts.persona_stability import compare

    # The mean of one score moves by 0.16 (16 personas one point up); nobody is 2 away.
    assert _marks(*_passes(100, {i: {"understood": 4} for i in range(16)})) == [
        True,
        False,
        True,
        True,
    ]
    assert _marks(*_passes(100, {i: {"understood": 4} for i in range(15)}))[1]
    # Opposite moves cancel in the mean (review R7-6): the per-persona mark still fails.
    cancel = {i: {"want_return": 5 if i % 2 else 1} for i in range(12)}
    first, again, ids = _passes(100, cancel)
    assert compare(first, again, ids)["scores"]["want_return"]["mean_shift"] == 0
    assert _marks(first, again, ids) == [True, True, False, True]
    # One persona with one different harm flag is enough.
    assert _marks(*_passes(100, {7: {"privacy": True}})) == [True, True, True, False]


def test_stability_counts_a_persona_once_and_reports_missing_scores() -> None:
    from scripts.persona_stability import compare

    first, again, ids = _passes(20, {0: {"understood": 5, "peaceful": 1}, 1: {"less_alone": 1}})
    del again["P020"]
    result = compare(first, again, ids)
    assert result["far_personas"] == ["P001", "P002"]
    assert (result["compared"], result["missing_b"]) == (19, ["P020"])
    assert result["scores"]["understood"]["far"] == 1
    # A pass that skipped someone cannot pass, whatever the other numbers say.
    assert _marks(first, again, ids) == [False, False, False, False]


def test_weighted_kappa_reads_agreement_not_only_equal_means() -> None:
    from scripts.persona_stability import weighted_kappa

    same = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
    flipped = [(1, 5), (2, 4), (3, 3), (4, 2), (5, 1)]
    assert weighted_kappa(same) == 1
    flipped_kappa = weighted_kappa(flipped)  # same mean, opposite reading
    assert flipped_kappa is not None and abs(flipped_kappa + 1) < 1e-9
    near = weighted_kappa([(1, 2), (2, 2), (3, 4), (4, 4), (5, 5)])
    assert near is not None and 0.8 < near < 1
    assert weighted_kappa([(3, 3), (3, 3)]) is None  # no spread: undefined, not "perfect"
    assert weighted_kappa([]) is None


def test_judge_output_is_refused_when_it_is_not_whole_scores_and_flags() -> None:
    import pytest

    from scripts.persona_stability import parse_scores

    assert parse_scores([_score("P001")])["P001"]["understood"] == 3
    for bad in (
        _score("P001", understood=6),
        _score("P001", understood=3.5),
        _score("P001", understood=True),
        _score("P001", privacy="no"),
        {"persona": "P001"},
    ):
        with pytest.raises(ValueError):
            parse_scores([bad])
    with pytest.raises(ValueError):
        parse_scores([_score("P001"), _score("P001")])


def test_packets_are_blind_and_each_pass_reads_in_its_own_order() -> None:
    from scripts.persona_metrics import JUDGED_DAYS
    from scripts.persona_stability import build_packets, split_for_pass

    people = _personas()[:12]
    rows = [
        {
            "persona": p["id"],
            "day": day,
            "status": 500 if (p["id"], day) == (people[0]["id"], 1) else 200,
            "mood": "Chill",
            "headline": f"Tiêu đề ngày {day}",
            "action": "Uống một cốc nước.",
        }
        for p in people
        for day in range(1, 30)
    ]
    packets = build_packets(people, rows)
    assert [p["persona"] for p in packets] == [p["id"] for p in people]
    assert len(packets[1]["days"]) == len(JUDGED_DAYS)
    assert len(packets[0]["days"]) == len(JUDGED_DAYS) - 1  # a failed day is not shown
    assert set(packets[0]) == {"persona", "profile", "days"}
    assert "day" not in packets[0]["days"][0]
    first = split_for_pass(packets, "first", 3)
    again = split_for_pass(packets, "again", 3)
    order = [[p["persona"] for p in batch] for batch in first]
    assert order != [[p["persona"] for p in batch] for batch in again]
    assert order == [[p["persona"] for p in batch] for batch in split_for_pass(packets, "first", 3)]
    assert {pid for batch in order for pid in batch} == {p["id"] for p in people}
    assert sum(len(batch) for batch in order) == len(people)
