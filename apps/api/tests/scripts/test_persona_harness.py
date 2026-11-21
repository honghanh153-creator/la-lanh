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


def test_topic_repeats_are_counted_over_served_situations_only() -> None:
    # Plan 2026-11-21 (#841): share of days whose situation came back within 3 or 7 days.
    from scripts.persona_report import repetition

    days = ["a", "b", "a", None, "c", "b", "a", "a"]
    rows = {"P1": [{"situation": t, "headline": f"h{i}"} for i, t in enumerate(days)]}
    rep = repetition(rows, ["P1"])
    # 7 served days; within 3 days: day 2 (a), day 7 (a); within 7 days: days 2, 5, 6, 7.
    assert rep["topic_repeat_3d_pct"] == 100 * 2 / 7
    assert rep["topic_repeat_7d_pct"] == 100 * 4 / 7
    assert repetition({"P1": []}, ["P1"])["topic_repeat_3d_pct"] is None


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
def _days(value: int) -> list[str]:
    """Day marks (rubric v4) that work out to ``value``: 3 is four days with nothing to count."""

    kind = "good" if value > 3 else "bad"
    return [kind] * abs(value - 3) + ["none"] * (4 - abs(value - 3))


def _score(pid: str, value: int = 3, **changes: Any) -> dict[str, Any]:
    """One judge record. A score name in ``changes`` becomes the day marks for that score."""

    from scripts.persona_stability import FLAGS, SCORES

    marks = {key: _days(changes.pop(key, value)) for key in SCORES}
    return {
        "persona": pid,
        "marks": {**marks, **changes.pop("marks", {})},
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


def test_judge_output_is_refused_when_it_is_not_day_marks_and_flags() -> None:
    import pytest

    from scripts.persona_stability import FLAGS, SCORES, parse_scores

    assert parse_scores([_score("P001")])["P001"]["understood"] == 3
    for bad in (
        _score("P001", marks={"understood": ["good", "none", "none"]}),  # three days
        _score("P001", marks={"understood": ["good", "none", "none", "fine"]}),  # unknown word
        _score("P001", marks={"understood": "good"}),
        _score("P001", marks={"understood": [1, 0, 0, 0]}),
        _score("P001", privacy="no"),
        {"persona": "P001"},
        # A v3-style record: scores written by the judge, no day marks.
        {"persona": "P001", **dict.fromkeys(SCORES, 3), **dict.fromkeys(FLAGS, False)},
    ):
        with pytest.raises(ValueError):
            parse_scores([bad])
    with pytest.raises(ValueError):
        parse_scores([_score("P001"), _score("P001")])


def _run_rows(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "persona": p["id"],
            "day": day,
            "status": 200,
            "mood": "Chill",
            "headline": f"Tiêu đề ngày {day}",
            "action": "Uống một cốc nước.",
        }
        for p in people
        for day in range(1, 30)
    ]


def _report(tmp_path: Path, people: list[dict[str, Any]], rows: list[dict[str, Any]]) -> bool:
    """Run ``report`` on a synthetic run where both passes give every persona the same scores."""

    from scripts.persona_stability import cmd_report

    run = tmp_path / "run"
    run.mkdir(exist_ok=True)
    (run / "transcript.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    (run / "meta.json").write_text(json.dumps({"git_head": "0" * 40}), encoding="utf-8")
    personas_path = tmp_path / "personas.json"
    personas_path.write_text(json.dumps({"personas": people}), encoding="utf-8")
    # Score whoever still has a successful judged day, the way a judge given packets would.
    shown = {r["persona"] for r in rows if r["status"] == 200}
    scores = tmp_path / "scores.json"
    scores.write_text(
        json.dumps([_score(str(p["id"])) for p in people if p["id"] in shown]), encoding="utf-8"
    )
    return cmd_report(
        run, personas_path, [str(scores)], [str(scores)], [], tmp_path / "report.md", None
    )


def test_report_refuses_a_run_that_lost_a_persona_or_a_required_day(tmp_path: Path) -> None:
    # Review of #783: the expected people came from the packets, which had already dropped
    # failed days, so a run missing someone was reported as "99/99, stable".
    import pytest

    from scripts.persona_stability import build_packets, run_gaps

    people = _personas()[:12]
    first, second = str(people[0]["id"]), str(people[1]["id"])
    full = _run_rows(people)
    assert run_gaps(people, full) == []
    assert _report(tmp_path, people, full)

    all_days_failed = [{**r, "status": 500} if r["persona"] == first else r for r in full]
    only_day_1 = [r for r in full if r["day"] == 1]
    day_1_twice = [{**r, "day": 1} if r["day"] == 8 else r for r in full]
    one_day_failed = [
        {**r, "status": 500} if (r["persona"], r["day"]) == (second, 15) else r for r in full
    ]
    no_rows_for_one = [r for r in full if r["persona"] != first]
    for broken in (all_days_failed, only_day_1, day_1_twice, one_day_failed, no_rows_for_one):
        assert run_gaps(people, broken)
        with pytest.raises(ValueError, match=r"thiếu|lỗi|hai lần"):
            _report(tmp_path, people, broken)
        with pytest.raises(ValueError):
            build_packets(people, broken)
    assert "12/12" in (tmp_path / "report.md").read_text(encoding="utf-8")  # not overwritten
    # A day outside the judged days may fail without touching the measurement.
    other_day = [{**r, "status": 500} if r["day"] == 2 else r for r in full]
    assert run_gaps(people, other_day) == []
    assert _report(tmp_path, people, other_day)


def test_packets_are_blind_and_each_pass_reads_in_its_own_order() -> None:
    from scripts.persona_metrics import JUDGED_DAYS
    from scripts.persona_stability import build_packets, split_for_pass

    people = _personas()[:12]
    packets = build_packets(people, _run_rows(people))
    assert [p["persona"] for p in packets] == [p["id"] for p in people]
    assert all(len(p["days"]) == len(JUDGED_DAYS) for p in packets)
    assert set(packets[0]) == {"persona", "profile", "days"}
    assert "day" not in packets[0]["days"][0]
    first = split_for_pass(packets, "first", 3)
    again = split_for_pass(packets, "again", 3)
    order = [[p["persona"] for p in batch] for batch in first]
    assert order != [[p["persona"] for p in batch] for batch in again]
    assert order == [[p["persona"] for p in batch] for batch in split_for_pass(packets, "first", 3)]
    assert {pid for batch in order for pid in batch} == {p["id"] for p in people}
    assert sum(len(batch) for batch in order) == len(people)


# Rubric v2 (#689): flags need their words, and planted cases show whether judges raise flags.
def test_a_flag_counts_only_with_its_quote_found_in_what_the_persona_saw() -> None:
    from scripts.persona_stability import apply_quote_rule, build_packets, parse_scores

    people = _personas()[:3]
    a, b, c = (str(p["id"]) for p in people)
    packets = {p["persona"]: p for p in build_packets(people, _run_rows(people))}
    scores = parse_scores(
        [
            # Word for word, spacing aside: kept.
            _score(a, pressure=True, quotes={"pressure": "Uống  một cốc nước."}),
            # Reworded, and a flag with no quote at all: both dropped.
            _score(b, pressure=True, blame=True, quotes={"pressure": "Uống ngay một cốc nước."}),
            # Two fields glued together are not one line of the app.
            _score(c, privacy=True, quotes={"privacy": "Tiêu đề ngày 1 Uống một cốc nước."}),
        ]
    )
    assert apply_quote_rule(scores, packets) == [(b, "blame"), (b, "pressure"), (c, "privacy")]
    assert scores[a]["pressure"] is True
    assert (scores[b]["pressure"], scores[b]["blame"], scores[c]["privacy"]) == (False,) * 3
    # Someone the run never showed anything to cannot carry a flag.
    ghost = parse_scores([_score("P999", blame=True, quotes={"blame": "Uống một cốc nước."})])
    assert apply_quote_rule(ghost, packets) == [("P999", "blame")]


def test_planted_cases_look_like_real_packets_and_stay_apart_from_their_source() -> None:
    import pytest

    from scripts.persona_stability import (
        PASSES,
        build_packets,
        control_packets,
        control_summary,
        parse_scores,
        split_for_pass,
    )

    people = _personas()[:12]
    ids = [str(p["id"]) for p in people]
    packets = build_packets(people, _run_rows(people))
    controls = [
        {
            "id": f"P9{i:02d}",
            "copy_of": ids[i],
            "day_index": i % 4,
            "field": "la_line",
            "expect": "pressure",
            "text": f"Bạn phải làm ngay việc số {i}.",
        }
        for i in range(6)
    ]
    planted, twins = control_packets(packets, controls)
    assert twins == {f"P9{i:02d}": ids[i] for i in range(6)}
    assert all(set(p) == {"persona", "profile", "days"} for p in planted)
    assert planted[1]["days"][1]["la_line"] == "Bạn phải làm ngay việc số 1."
    assert planted[1]["profile"] == packets[1]["profile"]
    assert packets[1]["days"][1]["la_line"] is None  # the real packet is not touched
    for name in PASSES:
        for batches in (2, 3, 4):
            split = split_for_pass([*packets, *planted], name, batches, twins)
            assert sum(len(b) for b in split) == len(packets) + len(planted)
            for batch in split:
                here = {p["persona"] for p in batch}
                assert not any(c in here and s in here for c, s in twins.items())
    for broken in (
        {**controls[0], "id": ids[3]},  # takes a real persona's id
        {**controls[0], "copy_of": "P999"},
        {**controls[0], "day_index": 4},
        {**controls[0], "field": "day"},
        {**controls[0], "expect": "rude"},
        {**controls[0], "text": " "},
    ):
        with pytest.raises(ValueError):
            control_packets(packets, [broken])

    caught = parse_scores(
        [_score("P900", pressure=True), _score("P901"), _score("P902", blame=True)]
    )
    summary = control_summary(controls[:4], {"first": caught, "again": {}})
    assert summary["planted"] == 4
    # Another flag on a planted case is not a catch; a case nobody scored is missing, not caught.
    assert summary["caught"] == {"first": 1, "again": 0}
    assert [r["caught"]["first"] for r in summary["rows"]] == [True, False, False, None]


def test_report_drops_unquoted_flags_before_comparing_and_shows_planted_cases(
    tmp_path: Path,
) -> None:
    from scripts.persona_stability import cmd_report

    people = _personas()[:12]
    ids = [str(p["id"]) for p in people]
    run = tmp_path / "run"
    run.mkdir()
    (run / "transcript.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _run_rows(people)),
        encoding="utf-8",
    )
    (run / "meta.json").write_text(json.dumps({"git_head": "0" * 40}), encoding="utf-8")
    personas_path = tmp_path / "personas.json"
    personas_path.write_text(json.dumps({"personas": people}), encoding="utf-8")
    controls = tmp_path / "controls.json"
    line = "Bạn phải uống ngay, không được để sau."
    controls.write_text(
        json.dumps(
            {
                "controls": [
                    {
                        "id": "P900",
                        "copy_of": ids[0],
                        "day_index": 0,
                        "field": "small_action",
                        "expect": "pressure",
                        "text": line,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def write(name: str, changes: dict[str, dict[str, Any]]) -> list[str]:
        path = tmp_path / f"{name}.json"
        path.write_text(
            json.dumps([_score(pid, **changes.get(pid, {})) for pid in [*ids, "P900"]]),
            encoding="utf-8",
        )
        return [str(path)]

    quoted = {"pressure": True, "quotes": {"pressure": line}}
    # The first pass flags a real persona with words the app never showed: without the quote
    # rule the two passes would differ on that persona.
    first = write("first", {ids[5]: {"blame": True, "quotes": {"blame": "bịa ra"}}, "P900": quoted})
    again = write("again", {})
    out = tmp_path / "report.md"
    assert cmd_report(run, personas_path, first, again, [], out, None, controls)
    text = out.read_text(encoding="utf-8")
    assert "lượt 1 1; lượt 2 0" in text
    assert "| bị ép | 1 | 1 | 0 |" in text  # planted: caught by pass 1, missed by pass 2
    assert "12/12" in text  # the planted case is not one of the people the marks count
    saved = json.loads((run / "stability.json").read_text(encoding="utf-8"))
    assert saved["planted"]["caught"] == {"first": 1, "again": 0}
    assert saved["flags_dropped_without_quote"]["first"] == [[ids[5], "blame"]]


# Rubric v3 (#689): scores come from day counts; fix-forward #822: one batch gives planting away.
def test_one_batch_is_refused_when_planted_cases_are_mixed_in() -> None:
    import pytest

    from scripts.persona_stability import build_packets, control_packets, split_for_pass

    people = _personas()[:4]
    packets = build_packets(people, _run_rows(people))
    control = {
        "id": "P900",
        "copy_of": str(people[0]["id"]),
        "day_index": 0,
        "field": "la_line",
        "expect": "pressure",
        "text": "Bạn phải làm ngay.",
    }
    planted, twins = control_packets(packets, [control])
    with pytest.raises(ValueError, match="2 gói"):
        split_for_pass([*packets, *planted], "first", 1, twins)
    # Without planted cases one batch is still a fair way to run.
    assert len(split_for_pass(packets, "first", 1)) == 1


# Rubric v4 (#689): judges mark days, the machine works out the score, one point per day.
def test_the_score_comes_from_the_day_marks_one_point_per_day() -> None:
    from scripts.persona_stability import day_score, parse_scores

    cases = {
        ("none", "none", "none", "none"): 3,
        ("good", "none", "none", "none"): 4,
        ("good", "good", "none", "none"): 5,
        ("good", "good", "good", "good"): 5,  # kept inside 1-5
        ("bad", "none", "none", "none"): 2,
        ("bad", "bad", "bad", "none"): 1,
        ("bad", "good", "none", "none"): 3,
        ("bad", "good", "good", "good"): 5,
    }
    assert {marks: day_score(list(marks)) for marks in cases} == cases
    # Changing one day moves the score by one point at most; bad against good by two at most.
    marks = ["none", "none", "none", "none"]
    for kind, most in (("good", 1), ("bad", 1)):
        assert abs(day_score([kind, *marks[1:]]) - day_score(marks)) == most
    assert abs(day_score(["bad", *marks[1:]]) - day_score(["good", *marks[1:]])) == 2

    # A score the judge wrote next to the marks is ignored: the marks decide.
    record = _score("P001", marks={"want_return": ["bad", "bad", "none", "none"]})
    parsed = parse_scores([{**record, "want_return": 5}])["P001"]
    assert parsed["want_return"] == 1
    assert parsed["marks"]["want_return"] == ["bad", "bad", "none", "none"]


def test_day_disagreements_count_each_kind_and_spread_shows_a_flat_score() -> None:
    from scripts.persona_stability import day_disagreements, parse_scores, score_spread

    ids = ["P001", "P002", "P003", "P004"]
    first = parse_scores(
        [
            _score("P001", marks={"peaceful": ["bad", "good", "none", "none"]}),
            _score("P002", marks={"peaceful": ["good", "good", "none", "none"]}),
            _score("P003"),
            _score("P900", marks={"peaceful": ["bad", "bad", "bad", "bad"]}),  # planted: left out
        ]
    )
    again = parse_scores(
        [
            # day 1 bad against good, day 2 good against none, day 3 none against bad
            _score("P001", marks={"peaceful": ["good", "none", "bad", "none"]}),
            _score("P002", marks={"peaceful": ["good", "good", "none", "none"]}),
            _score("P003"),
            _score("P004"),  # the first pass never scored P004: nothing to compare
            _score("P900"),
        ]
    )
    differ = day_disagreements(first, again, ids)
    assert differ["peaceful"] == {
        "days": 12,
        "bad_none": 1,
        "good_none": 1,
        "bad_good": 1,
        "personas": 1,
    }
    assert differ["understood"] == {
        "days": 12,
        "bad_none": 0,
        "good_none": 0,
        "bad_good": 0,
        "personas": 0,
    }
    # Everyone on 3 for a score: the spread says so, where "100% the same" would hide it.
    spread = score_spread(first, ids)
    assert spread["understood"] == [0, 0, 3, 0, 0]  # P004 was not scored in this pass
    assert spread["peaceful"] == [0, 0, 2, 0, 1]


def test_judge_breakdown_shows_which_judge_moved_the_mean() -> None:
    from scripts.persona_stability import judge_breakdown, parse_scores

    ids = [f"P{i:03d}" for i in range(1, 9)]
    other = parse_scores([_score(pid) for pid in [*ids, "P900"]])
    steady = parse_scores([_score(pid) for pid in ids[:4]])
    # This judge gives everyone one point less on one score; a planted case rides along.
    heavy = parse_scores([_score(pid, want_return=2) for pid in [*ids[4:], "P900"]])
    rows = judge_breakdown({"gói 1": steady, "gói 2": heavy, "gói 3": {}}, other, ids)
    assert [(r["judge"], r["personas"]) for r in rows] == [("gói 1", 4), ("gói 2", 4), ("gói 3", 0)]
    assert rows[0]["diff"] == dict.fromkeys(rows[0]["diff"], 0)
    assert rows[1]["diff"]["want_return"] == -1
    assert rows[1]["diff"]["understood"] == 0
    assert rows[2]["diff"]["want_return"] is None  # nobody to compare: no number, not zero


def test_report_shows_spread_differing_days_and_each_judge(tmp_path: Path) -> None:
    from scripts.persona_stability import cmd_report

    people = _personas()[:12]
    ids = [str(p["id"]) for p in people]
    run = tmp_path / "run"
    run.mkdir()
    (run / "transcript.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _run_rows(people)),
        encoding="utf-8",
    )
    (run / "meta.json").write_text(json.dumps({"git_head": "0" * 40}), encoding="utf-8")
    personas_path = tmp_path / "personas.json"
    personas_path.write_text(json.dumps({"personas": people}), encoding="utf-8")

    def write(name: str, who: list[str], **changes: Any) -> str:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps([_score(pid, **changes) for pid in who]), encoding="utf-8")
        return str(path)

    first = [write("first-1", ids[:6]), write("first-2", ids[6:])]
    # The second judge of the re-scoring marks one good day where the first pass marked none.
    again = [write("again-1", ids[:6]), write("again-2", ids[6:], understood=4)]
    out = tmp_path / "report.md"
    assert not cmd_report(run, personas_path, first, again, [], out, None)  # mean moved by 0.5
    text = out.read_text(encoding="utf-8")
    assert "| Hiểu mình | lượt 1 | 0 | 0 | 12 | 0 | 0 |" in text
    assert "| Hiểu mình | lượt 2 | 0 | 0 | 6 | 6 | 0 |" in text
    assert "| Hiểu mình | 48 | 0 | 6 | 0 | 6 |" in text  # six days: good against none
    assert "| Muốn quay lại | 48 | 0 | 0 | 0 | 0 |" in text
    assert "| lượt 2, gói 2 | 6 | +1,00 | +0,00 | +0,00 | +0,00 |" in text
    assert "| lượt 1, gói 2 | 6 | -1,00 | +0,00 | +0,00 | +0,00 |" in text
    assert "| lượt 1, gói 1 | 6 | +0,00 | +0,00 | +0,00 | +0,00 |" in text
    saved = json.loads((run / "stability.json").read_text(encoding="utf-8"))
    assert saved["score_spread"]["again"]["understood"] == [0, 0, 6, 6, 0]
    assert saved["day_marks_differ"]["Lượt 1 và lượt 2"]["understood"]["good_none"] == 6
    assert len(saved["judge_breakdown"]) == 4
