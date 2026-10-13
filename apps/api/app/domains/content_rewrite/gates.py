from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from app.domains.readings.companion import DIRECT_MAX_WORDS as COMPANION_REWRITE_MAX_WORDS
from app.domains.readings.daily_psychology import current_scene_lead
from app.domains.readings.models import DailyMeaningBrief
from app.domains.readings.review_agent import BANNED_CORE_FRAGMENTS, OPAQUE_CORE_FRAGMENTS


class DailyRewriteGateReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = "daily-home-rewrite-gates/v4"
    passed: bool
    failure_codes: tuple[str, ...] = ()


_WORD = re.compile(r"[^\W_]+(?:['-][^\W_]+)*", re.UNICODE)
_ASTRO_TERMS = (
    "mặt trời",
    "mặt trăng",
    "sao kim",
    "sao hỏa",
    "cung mọc",
    "nhà ",
    "tam hợp",
    "vuông góc",
    "transit",
)
_OPAQUE_FILLER = (
    "tín hiệu vũ trụ",
    "năng lượng đang mời gọi",
    "một lớp cần được soi",
    "dữ kiện vẫn cần được mời vào phòng",
    "nhịp bên trong",
)
_ACTION_VERBS = (
    "hỏi",
    "viết",
    "chọn",
    "đặt",
    "nói",
    "nhắn",
    "dừng",
    "kiểm tra",
    "đổi",
    "bỏ",
    "ghi",
    "xác nhận",
    "gửi",
    "xin",
    "giảm",
    "đọc",
)
_SCENE_MARKERS = (
    "khi ",
    "lúc ",
    "tin nhắn",
    "cuộc họp",
    "lịch",
    "câu trả lời",
    "đầu việc",
    "người kia",
    "ai đó",
    "nhóm",
)
_THEME_GROUPS = (
    ("tin nhắn", "nhắn", "nói", "hỏi", "câu", "trả lời"),
    ("việc", "lịch", "ưu tiên", "làm", "bỏ", "chọn", "tiến độ", "kết quả"),
    ("kế hoạch", "đổi", "xác nhận", "lịch"),
    ("giúp", "chăm", "đủ sức", "ranh giới", "từ chối"),
    ("chọn", "quyết định", "phân vân", "phương án"),
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace(
        "đ", "d"
    )


def _words(value: str) -> int:
    return len(_WORD.findall(unicodedata.normalize("NFC", value)))


def _theme_ids(text: str) -> frozenset[int]:
    folded = _fold(text)
    return frozenset(
        index
        for index, group in enumerate(_THEME_GROUPS)
        if any(_fold(term) in folded for term in group)
    )


# Lá never claims to know the reader, fate, or another person's mind (companion catalog).
_COMPANION_MIND_READING = (
    "lá biết",
    "số phận",
    "định mệnh",
    "người kia nghĩ",
    "người kia muốn",
    "họ đang nghĩ",
    "họ muốn",
)


def _companion_failures(companion: str, title: str, action: str) -> list[str]:
    failures: list[str] = []
    if not 4 <= _words(companion) <= COMPANION_REWRITE_MAX_WORDS:
        failures.append("daily_companion_budget")
    folded = _fold(companion)
    if any(_fold(term) in folded for term in _ASTRO_TERMS):
        failures.append("daily_companion_astro_term")
    if any(
        _fold(term) in folded
        for term in (*_OPAQUE_FILLER, *BANNED_CORE_FRAGMENTS, *OPAQUE_CORE_FRAGMENTS)
    ):
        failures.append("daily_companion_opaque_filler")
    if any(_fold(term) in folded for term in _COMPANION_MIND_READING):
        failures.append("daily_companion_mind_reading")
    if any(term in folded for term in ("chac chan", "nhat dinh", "se luon")):
        failures.append("daily_companion_certainty")
    # The bubble nudges; it must not restate the card next to it.
    stripped = folded.rstrip(" .!?")
    if stripped and (stripped in _fold(action) or stripped in _fold(title)):
        failures.append("daily_companion_repeats_card")
    if _fold(action).rstrip(" .!?") in folded:
        failures.append("daily_companion_repeats_card")
    return failures


def evaluate_daily_rewrite(
    output: Mapping[str, object],
    *,
    source_scene: str | None = None,
    source_action: str | None = None,
    meaning_brief: DailyMeaningBrief | None = None,
) -> DailyRewriteGateReport:
    failures: list[str] = []
    title = output.get("title")
    scene = output.get("scene")
    action = output.get("action")
    companion = output.get("companion")
    if not all(
        isinstance(value, str) and value.strip() for value in (title, scene, action, companion)
    ):
        return DailyRewriteGateReport(passed=False, failure_codes=("daily_required_fields",))
    title_text = str(title).strip()
    scene_text = str(scene).strip()
    action_text = str(action).strip()
    companion_text = str(companion).strip()
    if not 3 <= _words(title_text) <= 11:
        failures.append("daily_title_budget")
    if not 8 <= _words(scene_text) <= 40:
        failures.append("daily_scene_budget")
    if not 4 <= _words(action_text) <= 24:
        failures.append("daily_action_budget")
    if sum(_words(value) for value in (title_text, scene_text, action_text)) > 70:
        failures.append("daily_total_budget")
    failures.extend(_companion_failures(companion_text, title_text, action_text))
    if any(
        _words(sentence) > 28 for sentence in re.split(r"[.!?]+", scene_text) if sentence.strip()
    ):
        failures.append("daily_dense_sentence")
    folded = _fold(" ".join((title_text, scene_text, action_text)))
    if any(_fold(term) in folded for term in _ASTRO_TERMS):
        failures.append("daily_astro_term")
    if any(
        _fold(term) in folded
        for term in (*_OPAQUE_FILLER, *BANNED_CORE_FRAGMENTS, *OPAQUE_CORE_FRAGMENTS)
    ):
        failures.append("daily_opaque_filler")
    scene_folded = _fold(scene_text)
    action_folded = _fold(action_text)
    if re.search(r"(?:^|[.!?]\s+)(?:hay|thu|nen|dung)\s", scene_folded):
        failures.append("daily_advice_in_scene")
    if any(term in scene_folded for term in ("chac chan", "nhat dinh", "se luon", "luon luon")):
        failures.append("daily_unwarranted_certainty")
    if meaning_brief is not None:
        if not any(_fold(term) in scene_folded for term in meaning_brief.scene_anchors):
            failures.append("daily_scene_brief_drift")
        if not any(_fold(term) in action_folded for term in meaning_brief.action_anchors):
            failures.append("daily_action_brief_drift")
    if any(
        _fold(term) in scene_folded
        for term in ("đã gật", "đã đồng ý", "đã nhận lời", "đã nhận việc")
    ) and any(_fold(term) in action_folded for term in ("trước khi đồng ý", "trước khi nhận")):
        failures.append("daily_action_timing_conflict")
    if not any(_fold(marker) in scene_folded for marker in _SCENE_MARKERS):
        failures.append("daily_unobservable_scene")
    if not any(action_folded.startswith(_fold(verb)) for verb in _ACTION_VERBS):
        failures.append("daily_action_verb")
    if meaning_brief is None and not any(
        any(_fold(term) in scene_folded for term in group)
        and any(_fold(term) in action_folded for term in group)
        for group in _THEME_GROUPS
    ):
        failures.append("daily_scene_action_disconnected")
    if (
        meaning_brief is None
        and source_scene is not None
        and _theme_ids(source_scene)
        and not (_theme_ids(source_scene) & _theme_ids(scene_text))
    ):
        failures.append("daily_scene_meaning_drift")
    if (
        meaning_brief is None
        and source_action is not None
        and _theme_ids(source_action)
        and not (_theme_ids(source_action) & _theme_ids(action_text))
    ):
        failures.append("daily_action_meaning_drift")
    if source_scene is not None:
        # v7 opens the scene with one context clause ("Với người kia, khi …"). A rewrite
        # keeps it verbatim: dropping it loses the reader's chosen context, and the old
        # standalone fragment ("Ví dụ với người kia.") must not come back.
        lead = current_scene_lead(source_scene)
        if lead is not None and not scene_text.startswith(f"{lead} "):
            failures.append("daily_scene_context_lost")
        if re.search(r"(?:^|[.!?]\s+)vi du\b", scene_folded):
            failures.append("daily_scene_fragment")
        if meaning_brief is not None:
            # The thesis on the same card already ends with the takeaway; repeating it
            # in the title, scene or action says one idea twice.
            takeaway = _fold(meaning_brief.reader_takeaway).rstrip(" .!?")
            if takeaway and any(
                takeaway in _fold(value) for value in (title_text, scene_text, action_text)
            ):
                failures.append("daily_takeaway_repeated")
    unique = tuple(dict.fromkeys(failures))
    return DailyRewriteGateReport(passed=not unique, failure_codes=unique)
