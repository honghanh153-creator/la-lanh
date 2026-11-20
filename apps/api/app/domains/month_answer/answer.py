"""Compose a month answer from one transit fact and approved copy (AK2, 20.11.2026).

The three parts (theme, one thing to do now, one sentence to say) come from the copy registry as
``month.<part>.<topic>.<planet>``; nothing is served until Codex approves them (``approved_copy``
returns ``None`` while pending), so a topic with any pending part answers "not available" instead of
a half answer. The basis line is built from facts only: planet, sign and house names.

There are no dates here: the easier window is a separate request made only when the person taps
"Xem lúc nào dễ hơn".
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256

from app.domains.astro.models import BodyName, ZodiacSign
from app.domains.content.copy_approval import approved_copy
from app.domains.month_answer.facts import (
    ANSWER_PLANETS,
    FACTS_VERSION,
    EasierWindow,
    FactKind,
    HouseBasis,
    MonthFact,
    Topic,
)
from app.domains.month_answer.question import QuestionKind

ANSWER_VERSION = "month-answer-v1"
PARTS = ("theme", "act", "say")
LINE_IDS = ("month.line.disclaimer", "month.line.window")
REFRAME_KINDS = (
    QuestionKind.OUTCOME,
    QuestionKind.TIMING,
    QuestionKind.SHOULD,
    QuestionKind.OTHER_MIND,
)

TOPIC_LABELS: dict[Topic, str] = {
    Topic.WORK: "Công việc",
    Topic.MONEY: "Tiền",
    Topic.LOVE: "Tình cảm",
    Topic.FAMILY: "Gia đình",
    Topic.STUDY: "Học",
    Topic.MIND: "Sức khỏe tinh thần",
}

PLANET_NAMES: dict[BodyName, str] = {
    BodyName.SUN: "Mặt Trời",
    BodyName.MOON: "Mặt Trăng",
    BodyName.MERCURY: "Sao Thủy",
    BodyName.VENUS: "Sao Kim",
    BodyName.MARS: "Sao Hỏa",
    BodyName.JUPITER: "Sao Mộc",
    BodyName.SATURN: "Sao Thổ",
}

SIGN_NAMES: dict[ZodiacSign, str] = dict(
    zip(
        ZodiacSign,
        (
            "Bạch Dương",
            "Kim Ngưu",
            "Song Tử",
            "Cự Giải",
            "Sư Tử",
            "Xử Nữ",
            "Thiên Bình",
            "Bọ Cạp",
            "Nhân Mã",
            "Ma Kết",
            "Bảo Bình",
            "Song Ngư",
        ),
        strict=True,
    )
)

HOUSE_LABELS: dict[int, str] = {
    1: "bản thân",
    2: "tiền bạc",
    3: "học hỏi",
    4: "gia đình",
    5: "tình cảm",
    6: "việc hằng ngày",
    7: "các mối quan hệ",
    8: "tiền chung",
    9: "học xa",
    10: "công việc",
    11: "bạn bè",
    12: "nghỉ ngơi",
}

CopySource = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class Basis:
    line: str
    detail: str


@dataclass(frozen=True, slots=True)
class MonthAnswer:
    month: str
    topic: Topic
    topic_label: str
    reframe: str | None
    theme: str
    act: str
    say: str
    basis: Basis
    disclaimer: str
    answer_key: str  # stable id of (facts, copy ids, kind): what "Lưu" stores


def copy_ids(topic: Topic, planet: BodyName) -> tuple[str, ...]:
    return tuple(f"month.{part}.{topic.value}.{planet.value}" for part in PARTS)


def required_copy_ids() -> tuple[str, ...]:
    """Every sentence an answer can need. The feature shows only when all are approved."""

    ids = [cid for topic in Topic for planet in ANSWER_PLANETS for cid in copy_ids(topic, planet)]
    ids += [f"month.reframe.{kind.value}" for kind in REFRAME_KINDS]
    ids += list(LINE_IDS)
    return tuple(ids)


def feature_ready(source: CopySource = approved_copy) -> bool:
    return all(source(cid) is not None for cid in required_copy_ids())


def compose(
    fact: MonthFact,
    kind: QuestionKind = QuestionKind.HOW,
    source: CopySource = approved_copy,
) -> MonthAnswer | None:
    """The answer, or ``None`` while any sentence it needs is not approved."""

    ids = copy_ids(fact.topic, fact.planet)
    parts = [source(cid) for cid in ids]
    disclaimer = source("month.line.disclaimer")
    reframe_id = f"month.reframe.{kind.value}" if kind in REFRAME_KINDS else None
    reframe = source(reframe_id) if reframe_id else None
    if any(part is None for part in parts) or disclaimer is None:
        return None
    if reframe_id is not None and reframe is None:
        return None
    theme, act, say = (part for part in parts if part is not None)
    key_material = "|".join(
        (
            ANSWER_VERSION,
            FACTS_VERSION,
            fact.month,
            fact.topic.value,
            fact.kind.value,
            fact.planet.value,
            fact.house_basis.value,
            str(fact.house),
            fact.sign.value,
            kind.value,
            *ids,
        )
    )
    return MonthAnswer(
        month=fact.month,
        topic=fact.topic,
        topic_label=TOPIC_LABELS[fact.topic],
        reframe=reframe,
        theme=theme,
        act=act,
        say=say,
        basis=basis_for(fact),
        disclaimer=disclaimer,
        answer_key=sha256(key_material.encode()).hexdigest()[:32],
    )


def basis_for(fact: MonthFact) -> Basis:
    planet = PLANET_NAMES[fact.planet]
    sign = SIGN_NAMES[fact.sign]
    counted = (
        f" Nhà tính theo cung Mặt Trời {SIGN_NAMES[fact.solar_sign]} của bạn."
        if fact.house_basis is HouseBasis.SOLAR and fact.solar_sign is not None
        else ""
    )
    if fact.kind is FactKind.IN_HOUSE and fact.house is not None:
        label = HOUSE_LABELS[fact.house]
        return Basis(
            line=f"Dựa vào: {planet} đi qua nhà {label} của bạn.",
            detail=(
                f"Tháng này {planet} ở cung {sign}, trong nhà {fact.house} của bạn. "
                f"Nhà {fact.house} là nhà {label}.{counted}"
            ),
        )
    if fact.kind is FactKind.RULER and fact.ruled_house is not None:
        ruled_label = HOUSE_LABELS[fact.ruled_house]
        ruled_sign = SIGN_NAMES[fact.ruled_sign] if fact.ruled_sign else ""
        opening = (
            f"Nhà {fact.ruled_house} của bạn (nhà {ruled_label}) bắt đầu ở cung {ruled_sign}, "
            f"sao chủ của cung này là {planet}."
        )
        if fact.house is None:
            return Basis(
                line=f"Dựa vào: {planet}, sao chủ nhà {ruled_label} của bạn.",
                detail=f"{opening} {planet} đi qua đủ các nhà trong một tháng.{counted}",
            )
        return Basis(
            line=(
                f"Dựa vào: {planet}, sao chủ nhà {ruled_label} của bạn, "
                f"tháng này ở nhà {HOUSE_LABELS[fact.house]}."
            ),
            detail=(
                f"{opening} Tháng này {planet} ở cung {sign}, trong nhà {fact.house} của bạn."
                f"{counted}"
            ),
        )
    return Basis(
        line=f"Dựa vào: {planet} tháng này ở cung {sign}.",
        detail=f"Lá dựa vào vị trí của {planet} trên trời tháng này.",
    )


@dataclass(frozen=True, slots=True)
class WindowAnswer:
    start: str  # ISO date
    end: str
    basis: str
    line: str


def window_answer(window: EasierWindow, source: CopySource = approved_copy) -> WindowAnswer | None:
    line = source("month.line.window")
    if line is None:
        return None
    if window.house is not None:
        basis = f"Dựa vào: Mặt Trăng đi qua nhà {HOUSE_LABELS[window.house]} của bạn."
    elif window.sign is not None:
        basis = f"Dựa vào: Mặt Trăng đi qua cung {SIGN_NAMES[window.sign]}."
    else:
        basis = "Dựa vào: vị trí của Mặt Trăng."
    return WindowAnswer(
        start=window.start.isoformat(), end=window.end.isoformat(), basis=basis, line=line
    )
