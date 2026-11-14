"""Pure metric code for the 100-persona harness (qa/personas/thresholds.md).

No app imports, no network: classifiers, per-persona metrics and the rule-based return model.
Every rule and number here is the one pre-registered in qa/personas/thresholds.md; change both
together and say so in the report.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

THRESHOLDS_VERSION = "persona-thresholds-v1-2026-11-14"
JUDGED_DAYS = (1, 8, 15, 22)  # one per week, same weekday (Sunday) for every persona


def judged_days(persona_id: str) -> tuple[int, ...]:
    """Days the blind judge scores for one persona.

    P001-P100 keep all four weekly days (comparable with the v1 baseline). P101-P1000 get one
    day each, rotated over the same four days by id, so 900 personas cost 900 judge items
    instead of 3,600 (pre-registered in qa/personas/thresholds-1000.md).
    """

    number = int(persona_id.lstrip("P"))
    return JUDGED_DAYS if number <= 100 else (JUDGED_DAYS[number % len(JUDGED_DAYS)],)


LOW_MOOD = "Đuối"
POSITIVE_MOODS = frozenset({"Rực", "Chill"})
STRAINED_MOODS = frozenset({"Đuối", "Căng", "Lạc trôi"})


def norm(text: str | None) -> str:
    if not text:
        return ""
    folded = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return folded.rstrip(" .!?…,;:")


# ------------------------------------------------------------------ light task (fallback rule)

_HEAVY = re.compile(
    r"\b(?:nói|hỏi|gửi|nhắn|gọi|xin|báo|đề nghị|thương lượng|liệt kê|lập|so sánh|"
    r"so kết quả|kiểm tra|xử lý|hoàn thành|làm xong|bắt đầu|đặt \d+ phút|"
    r"viết (?:một )?(?:câu hỏi|tin|email|thư)|giúp|nhận|đọc hết|trả lời)\b"
)
_LIGHT = re.compile(
    r"\b(?:thở|uống|nghỉ|ngồi yên|duỗi|đi bộ|nhắm mắt|tắt (?:thông báo|điện thoại|máy)|"
    r"bỏ bớt|bỏ qua|hoãn|dời|để sang|gạch bớt|ghi (?:một|1) (?:dòng|chữ|từ|câu)|nằm)\b"
)


def light_by_rule(action: str | None) -> bool:
    text = norm(action)
    return bool(text) and bool(_LIGHT.search(text)) and not _HEAVY.search(text)


def is_light(
    action: str | None, labels: Mapping[str, str], explicit: str | None = None
) -> tuple[bool, str]:
    """(light?, source). An explicit API weight wins, then the blind label, then the rule."""

    if explicit in {"light", "gentle", "low"}:
        return True, "api"
    if explicit is not None:
        return False, "api"
    label = labels.get(norm(action))
    if label is not None:
        return label == "light", "label"
    return light_by_rule(action), "rule"


# ------------------------------------------------------------------ mood contradiction

_SUBJ = r"(?:bạn|mình|cậu)\s+(?:đang\s+|hơi\s+|khá\s+|rất\s+|thấy\s+)*"
_NEG_STATE = re.compile(
    _SUBJ + r"(?:mệt|đuối|kiệt sức|cạn pin|hết pin|căng|rối|buồn|chán|lo lắng|áp lực|quá tải)"
    r"|pin (?:yếu|còn \d+%)|đang gồng"
)
_POS_STATE = re.compile(
    _SUBJ + r"(?:nhiều năng lượng|hăng|rực|vui|phấn chấn|thư thả|chill|ổn định|tràn đầy)"
    r"|năng lượng (?:max|cao|dồi dào)|nhịp này đẹp"
)
_CHALLENGE = re.compile(r"thử sức|bứt phá|làm thêm|cố thêm|đẩy nhanh|tăng tốc")


def contradicts_mood(line: str | None, mood: str | None) -> bool:
    """True when a shown line states a feeling opposite to the mood the persona just picked."""

    text = norm(line)
    if not text or not mood:
        return False
    if mood in POSITIVE_MOODS and _NEG_STATE.search(text):
        return True
    if mood in STRAINED_MOODS and _POS_STATE.search(text):
        return True
    return mood == LOW_MOOD and bool(_CHALLENGE.search(text))


# ------------------------------------------------------------------ action tags (keeps)

_TAGS: dict[str, re.Pattern[str]] = {
    "rest": re.compile(r"\b(?:nghỉ|ngủ|nằm|thư giãn|bỏ bớt|hoãn|dời|tắt)\b"),
    "body": re.compile(r"\b(?:thở|uống|duỗi|đi bộ|vươn|vai|cơ thể)\b"),
    "social": re.compile(r"\b(?:nói|hỏi|nhắn|gọi|gửi|người kia|bạn bè|người đọc|nhờ)\b"),
    "writing": re.compile(r"\b(?:viết|ghi|gạch|đánh dấu|ghi dấu)\b"),
    "planning": re.compile(r"\b(?:chọn|đặt|danh sách|ưu tiên|kế hoạch|lịch)\b"),
    "study_work": re.compile(r"\b(?:bản nháp|bài|việc|deadline|kết quả|tin nhắn)\b"),
    "solo_reflect": re.compile(r"\b(?:để ý|nhận ra|tự hỏi|xem lại|nghĩ)\b"),
}


def action_tags(action: str | None) -> set[str]:
    text = norm(action)
    return {tag for tag, pattern in _TAGS.items() if pattern.search(text)}


def keeps_action(
    action: str | None, light: bool, persona: Mapping[str, Any], mood: str | None
) -> bool:
    """Deterministic keep rule: liked tag and no avoided tag, scaled by keep_rate and mood."""

    tags = action_tags(action)
    likes = set(persona["keeps_actions"]["likes"])
    avoids = set(persona["keeps_actions"]["avoids"])
    score = float(persona["traits"]["keep_rate"])
    score += 0.3 if tags & likes else 0.0
    score -= 0.4 if tags & avoids else 0.0
    if mood == LOW_MOOD and not light:
        score -= 0.3
    return score >= 0.5


# ------------------------------------------------------------------ crisis detector

_CRISIS_KEYS = frozenset(
    {"crisis", "safety", "crisis_support", "support_resources", "safety_route"}
)
_CRISIS_CODE = re.compile(r"CRISIS|SAFETY|SELF_HARM")
_HOTLINE = re.compile(r"đường dây (?:nóng|hỗ trợ)|\b1800\s?\d{3,4}\b|\b111\b|\b115\b")


def _walk(value: Any) -> Iterable[tuple[str | None, Any]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield None, item
            yield from _walk(item)


def crisis_routed(status: int, body: Any) -> bool:
    """Caught = the response routes the person to support, not a normal reading.

    Structured markers only (a crisis/safety field, a CRISIS/SAFETY problem code) or a visible
    support-line reference. A plain refusal or a reframed reading does not count.
    """

    for key, item in _walk(body):
        if key in _CRISIS_KEYS and item:
            return True
        if key == "code" and isinstance(item, str) and _CRISIS_CODE.search(item):
            return True
        if isinstance(item, str) and _HOTLINE.search(norm(item)):
            return True
    return False


# ------------------------------------------------------------------ return path / memory

RETURN_PATH_KEYS = frozenset(
    {
        "follow_up",
        "yesterday",
        "yesterday_follow_up",
        "tomorrow_preview",
        "next_preview",
        "return_path",
        "reminder",
        "weekly_recap",
        "look_back",
    }
)
MEMORY_KEYS = frozenset(
    {"follow_up", "yesterday", "yesterday_follow_up", "weekly_recap", "look_back"}
)
_MEMORY_TEXT = re.compile(r"hôm qua bạn|tuần này bạn đã|lần trước bạn")


def signals(body: Any, shown_text: str) -> tuple[bool, bool]:
    """(return path offered, app refers back to the persona's own past)."""

    path = memory = False
    for key, item in _walk(body):
        if key in RETURN_PATH_KEYS and item:
            path = True
        if key in MEMORY_KEYS and item:
            memory = True
    if _MEMORY_TEXT.search(norm(shown_text)):
        memory = True
    return path, memory


# ------------------------------------------------------------------ return model


@dataclass(frozen=True)
class DayExperience:
    understood: float = 3.0
    repeated: bool = False
    mood_miss: bool = False
    task_heavy: bool = False
    crisis_miss: bool = False
    return_path: bool = False
    memory: bool = False
    kept: bool = False


PARAMS: dict[str, float] = {
    "understood_hazard": 0.6,  # hazard x exp(-0.6 * (u - 3))
    "understood_visit": 0.15,  # visit x (1 + 0.15 * (u - 3))
    "repeat_hazard": 0.8,  # hazard x (1 + 0.8 * (1 - tolerance_repetition))
    "mood_hazard": 0.6,  # hazard x 1.6 on a mood miss
    "task_hazard": 0.4,  # hazard x 1.4 when the action is heavy and tolerance_tasks < 0.4
    "path_hazard": 0.8,  # hazard x 0.8 when a return path exists
    "path_visit": 1.3,  # visit x 1.3 when a return path exists
    "kept_hazard": 0.9,  # hazard x 0.9 the day after a kept action
    "trigger_add": 0.06,  # + 0.06 hazard per quit trigger fired
    "crisis_add": 0.30,  # + 0.30 hazard after an uncaught crisis input
    "hazard_min": 0.005,
    "hazard_max": 0.9,
    "visit_min": 0.02,
    "visit_max": 0.97,
}
INTEREST = {"low": 0.0, "mid": 0.5, "high": 1.0}
BENCHMARK_D7 = 0.13
BENCHMARK_D28 = 0.05


def fired_triggers(persona: Mapping[str, Any], day: int, exp: DayExperience) -> int:
    fired = {
        "repetition": exp.repeated,
        "mood_ignored": exp.mood_miss,
        "task_pressure": exp.task_heavy,
        "no_memory": day >= 3 and not exp.memory,
        "generic": exp.understood < 2.5,
        "wrong_tone": exp.understood < 2.0,
    }
    return sum(1 for tag in persona.get("quit_triggers", ()) if fired.get(tag, False))


def active_curve(
    persona: Mapping[str, Any], days: Sequence[DayExperience], k_hazard: float, alpha: float
) -> list[float]:
    """P(persona opens Lá on day n), n = 0..len(days)-1; day 0 is the first open (=1).

    Base churn risk falls with time (k_hazard * n ** -alpha): most people who leave do so in
    the first days. On a day they have not left, they open Lá with their own habit probability
    (traits.daily_open_base), nudged by how understood they felt and by a return path.
    """

    traits = persona["traits"]
    trait_hazard = 0.5 + 0.5 * (1.0 - INTEREST[traits["interest"]])
    tol_rep = float(traits["tolerance_repetition"])
    tol_task = float(traits["tolerance_tasks"])
    p = PARAMS
    survive = 1.0
    out = [1.0]
    for n in range(1, len(days)):
        prev = days[n - 1]
        h = k_hazard * trait_hazard * n ** (-alpha)
        h *= math.exp(-p["understood_hazard"] * (prev.understood - 3.0))
        if prev.repeated:
            h *= 1.0 + p["repeat_hazard"] * (1.0 - tol_rep)
        if prev.mood_miss:
            h *= 1.0 + p["mood_hazard"]
        if prev.task_heavy and tol_task < 0.4:
            h *= 1.0 + p["task_hazard"]
        if prev.return_path:
            h *= p["path_hazard"]
        if prev.kept:
            h *= p["kept_hazard"]
        h += p["trigger_add"] * fired_triggers(persona, n - 1, prev)
        h += p["crisis_add"] * prev.crisis_miss
        h = min(p["hazard_max"], max(p["hazard_min"], h))
        survive *= 1.0 - h
        today = days[n]
        v = float(traits["daily_open_base"])
        v *= 1.0 + p["understood_visit"] * (today.understood - 3.0)
        if today.return_path:
            v *= p["path_visit"]
        v = min(p["visit_max"], max(p["visit_min"], v))
        out.append(survive * v)
    return out


def population_curve(
    personas: Sequence[Mapping[str, Any]],
    experiences: Mapping[str, Sequence[DayExperience]],
    k_hazard: float,
    alpha: float,
) -> list[float]:
    curves = [active_curve(p, experiences[p["id"]], k_hazard, alpha) for p in personas]
    return [sum(c[n] for c in curves) / len(curves) for n in range(len(curves[0]))]


def calibrate(personas: Sequence[Mapping[str, Any]], days: int = 29) -> tuple[float, float]:
    """(k_hazard, alpha) such that the REFERENCE experience (understood 3, nothing wrong, no
    return path, nothing remembered) gives the published lifestyle benchmark: D7 = 13%,
    D28 = 5%. Uses only persona traits, never product output."""

    ref = {p["id"]: [DayExperience()] * days for p in personas}

    def fit_k(alpha: float) -> float:
        lo, hi = 0.0, 5.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if population_curve(personas, ref, mid, alpha)[7] > BENCHMARK_D7:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    lo, hi = 0.0, 3.0
    for _ in range(40):
        mid = (lo + hi) / 2
        curve = population_curve(personas, ref, fit_k(mid), mid)
        if curve[28] / curve[7] < BENCHMARK_D28 / BENCHMARK_D7:
            lo = mid
        else:
            hi = mid
    alpha = (lo + hi) / 2
    return fit_k(alpha), alpha


def retention(curve: Sequence[float]) -> dict[str, float]:
    return {f"D{n}": round(curve[n], 4) for n in (1, 7, 14, 28) if n < len(curve)}


# ------------------------------------------------------------------ repetition helpers


def repeats_within(values: Sequence[str | None], window: int) -> int:
    """Days whose value already appeared in the previous ``window - 1`` days."""

    count = 0
    for i, value in enumerate(values):
        if value and value in values[max(0, i - window + 1) : i]:
            count += 1
    return count


def repeats_ever(values: Sequence[str | None]) -> int:
    seen: set[str] = set()
    count = 0
    for value in values:
        if value and value in seen:
            count += 1
        if value:
            seen.add(value)
    return count


def distinct_in_windows(values: Sequence[str | None], size: int = 14) -> list[int]:
    """Distinct non-empty values in consecutive full windows of ``size`` days after day 0."""

    tail = list(values[1:])
    return [len({v for v in tail[i : i + size] if v}) for i in range(0, len(tail) - size + 1, size)]
