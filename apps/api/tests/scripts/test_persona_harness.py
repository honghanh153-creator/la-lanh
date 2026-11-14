import json
from pathlib import Path

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
