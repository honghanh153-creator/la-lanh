"""Lean, linked summary and dynamic headline for framed Tarot readings (US-20 AC08-AC11, B2-3).

Everything here is authored copy or a deterministic rule over closed labels; nothing is taken
from the question's text. New copy needs owner approval before release, and this module joins
the fallback approval scope then (docs/plans/2026-10-18-b2-3-tarot-stance-task.md).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from app.domains.tarot import question_frame
from app.domains.tarot.models import (
    TarotAction,
    TarotContext,
    TarotQuestionForm,
    TarotStance,
    TarotStanceKind,
    TarotStanceLevel,
    TarotStanceReason,
)
from app.domains.tarot.roles import ROLES, RoleField

STANCE_VERSION = "tarot-stance-v1"


class Lean(StrEnum):
    OPEN = "open"  # mở: supports trying the action
    HOLD = "hold"  # giữ: asks for more care first
    TWO_SIDED = "two_sided"  # hai mặt


_VALUE = {Lean.OPEN: 1.0, Lean.HOLD: -1.0, Lean.TWO_SIDED: 0.0}

# Default lean per card (upright reading conventions), then topic overrides only where they
# differ. 78 defaults + overrides, within the 468-label budget of US-20 AC09.
LEAN_DEFAULTS: dict[str, Lean] = {
    "major-fool": Lean.OPEN,
    "major-magician": Lean.OPEN,
    "major-high-priestess": Lean.HOLD,
    "major-empress": Lean.OPEN,
    "major-emperor": Lean.TWO_SIDED,
    "major-hierophant": Lean.TWO_SIDED,
    "major-lovers": Lean.TWO_SIDED,
    "major-chariot": Lean.OPEN,
    "major-strength": Lean.OPEN,
    "major-hermit": Lean.HOLD,
    "major-wheel-of-fortune": Lean.TWO_SIDED,
    "major-justice": Lean.TWO_SIDED,
    "major-hanged-man": Lean.HOLD,
    "major-death": Lean.HOLD,
    "major-temperance": Lean.TWO_SIDED,
    "major-devil": Lean.HOLD,
    "major-tower": Lean.HOLD,
    "major-star": Lean.OPEN,
    "major-moon": Lean.HOLD,
    "major-sun": Lean.OPEN,
    "major-judgement": Lean.OPEN,
    "major-world": Lean.OPEN,
    "wands-ace": Lean.OPEN,
    "wands-2": Lean.OPEN,
    "wands-3": Lean.OPEN,
    "wands-4": Lean.OPEN,
    "wands-5": Lean.TWO_SIDED,
    "wands-6": Lean.OPEN,
    "wands-7": Lean.TWO_SIDED,
    "wands-8": Lean.OPEN,
    "wands-9": Lean.HOLD,
    "wands-10": Lean.HOLD,
    "wands-page": Lean.OPEN,
    "wands-knight": Lean.OPEN,
    "wands-queen": Lean.OPEN,
    "wands-king": Lean.OPEN,
    "cups-ace": Lean.OPEN,
    "cups-2": Lean.OPEN,
    "cups-3": Lean.OPEN,
    "cups-4": Lean.HOLD,
    "cups-5": Lean.HOLD,
    "cups-6": Lean.TWO_SIDED,
    "cups-7": Lean.HOLD,
    "cups-8": Lean.TWO_SIDED,
    "cups-9": Lean.OPEN,
    "cups-10": Lean.OPEN,
    "cups-page": Lean.OPEN,
    "cups-knight": Lean.OPEN,
    "cups-queen": Lean.TWO_SIDED,
    "cups-king": Lean.TWO_SIDED,
    "swords-ace": Lean.OPEN,
    "swords-2": Lean.HOLD,
    "swords-3": Lean.HOLD,
    "swords-4": Lean.HOLD,
    "swords-5": Lean.HOLD,
    "swords-6": Lean.OPEN,
    "swords-7": Lean.HOLD,
    "swords-8": Lean.HOLD,
    "swords-9": Lean.HOLD,
    "swords-10": Lean.HOLD,
    "swords-page": Lean.TWO_SIDED,
    "swords-knight": Lean.TWO_SIDED,
    "swords-queen": Lean.TWO_SIDED,
    "swords-king": Lean.TWO_SIDED,
    "pentacles-ace": Lean.OPEN,
    "pentacles-2": Lean.TWO_SIDED,
    "pentacles-3": Lean.OPEN,
    "pentacles-4": Lean.HOLD,
    "pentacles-5": Lean.HOLD,
    "pentacles-6": Lean.OPEN,
    "pentacles-7": Lean.HOLD,
    "pentacles-8": Lean.OPEN,
    "pentacles-9": Lean.OPEN,
    "pentacles-10": Lean.OPEN,
    "pentacles-page": Lean.OPEN,
    "pentacles-knight": Lean.TWO_SIDED,
    "pentacles-queen": Lean.OPEN,
    "pentacles-king": Lean.OPEN,
}
LEAN_OVERRIDES: dict[tuple[str, TarotContext], Lean] = {
    ("major-lovers", TarotContext.RELATIONSHIPS): Lean.OPEN,
    ("cups-8", TarotContext.SELF_CARE): Lean.OPEN,
    ("cups-8", TarotContext.ENERGY): Lean.OPEN,
}


def lean_of(card_id: str, topic: TarotContext) -> Lean:
    return LEAN_OVERRIDES.get((card_id, topic), LEAN_DEFAULTS[card_id])


def role_weight(position_key: str) -> float:
    role = ROLES[position_key]
    if role.step:
        return 2.0
    return 0.5 if role.field is RoleField.TENSION else 1.0


# Approved verb phrases for {action}; never text from the question.
ACTION_PHRASES: dict[TarotAction, str] = {
    TarotAction.NHAN_LOI: "nhận lời",
    TarotAction.TU_CHOI: "từ chối",
    TarotAction.NOI_RA: "nói ra điều mình nghĩ",
    TarotAction.NHAN_LAI: "nhắn lại",
    TarotAction.HOI_LAI: "hỏi lại cho rõ",
    TarotAction.CHO_THEM: "chờ thêm một chút",
    TarotAction.BAT_DAU: "bắt đầu",
    TarotAction.DUNG_LAI: "dừng lại",
    TarotAction.DOI_VIEC: "đổi hướng công việc",
    TarotAction.XIN_GOP_Y: "xin góp ý",
    TarotAction.NGHI_NGOI: "nghỉ ngơi",
    TarotAction.GUI_DI: "gửi đi",
    TarotAction.XIN_LOI: "xin lỗi",
    TarotAction.HEN_GAP: "hẹn gặp",
    TarotAction.CHIA_SE: "chia sẻ",
    TarotAction.DAT_RANH_GIOI: "đặt ranh giới",
    TarotAction.KET_THUC: "kết thúc",
    TarotAction.THU_LAI: "thử lại",
    TarotAction.HOC_THEM: "học thêm",
    TarotAction.TAP_TRUNG: "tập trung vào một việc",
    TarotAction.SAP_XEP_LAI: "sắp xếp lại",
    TarotAction.NHO_GIUP: "nhờ giúp",
    TarotAction.GOP_Y: "góp ý",
    TarotAction.DE_XUAT: "đề xuất",
    TarotAction.DON_DEP: "dọn dẹp",
    TarotAction.RA_NGOAI: "ra ngoài",
    TarotAction.O_NHA: "ở nhà",
    TarotAction.DOI_THOI_QUEN: "đổi thói quen",
    TarotAction.TU_THUONG: "tự thưởng cho mình",
    TarotAction.VIET_RA: "viết ra",
}
GENERIC_ACTION = "làm điều bạn đang cân nhắc"

# Three levels (no "lean to not doing it") plus the choice fallback. Each conclusion carries a
# marker the stance_consistent gate looks for in the headline and forbids elsewhere.
CONCLUSIONS: dict[TarotStanceLevel, str] = {
    TarotStanceLevel.LEAN_TRY: "Các lá nghiêng về thử {action}.",
    TarotStanceLevel.CONSIDER: "Các lá gợi ý cân nhắc thêm trước khi {action}.",
    TarotStanceLevel.UNCLEAR: "Chưa rõ: các lá kéo về hai phía.",
    TarotStanceLevel.CLARIFY_CHOICE: (
        "Trải bài này chưa so được hai hướng; hãy xem điều cần rõ trước khi chọn."
    ),
}
MARKERS: dict[TarotStanceLevel, str] = {
    TarotStanceLevel.LEAN_TRY: "nghiêng về thử",
    TarotStanceLevel.CONSIDER: "cân nhắc thêm trước khi",
    TarotStanceLevel.UNCLEAR: "kéo về hai phía",
    TarotStanceLevel.CLARIFY_CHOICE: "cần rõ trước khi chọn",
}

TOPIC_PHRASES: dict[TarotContext, str] = {
    TarotContext.GENERAL: "chuyện này",
    TarotContext.RELATIONSHIPS: "chuyện tình cảm",
    TarotContext.WORK: "công việc",
    TarotContext.COMMUNICATION: "cuộc trò chuyện",
    TarotContext.ENERGY: "nhịp năng lượng",
    TarotContext.SELF_CARE: "việc chăm mình",
}
# Headline = form + lean (or action/topic) + focal card (+ the pitfall card when there is one).
HEADLINES: dict[str, str] = {
    TarotStanceLevel.LEAN_TRY.value: "{focal}: các lá nghiêng về thử {action}.",
    TarotStanceLevel.CONSIDER.value: "{focal}: cân nhắc thêm trước khi {action}.",
    TarotStanceLevel.UNCLEAR.value: "{focal}: chuyện {action} còn kéo về hai phía.",
    TarotStanceLevel.CLARIFY_CHOICE.value: "{pair}: điều cần rõ trước khi chọn.",
    TarotQuestionForm.TIMING.value: "{focal}: điều cần sẵn sàng trước khi {action}.",
    TarotQuestionForm.HOW.value: "{pair}: một cách bắt đầu {target}.",
    TarotQuestionForm.WHY.value: "{pair}: một lý do đáng soi trong {topic}.",
    TarotQuestionForm.OPEN.value: "{pair}: điều đáng nhìn rõ trong {topic}.",
}

# Conjunctions by the role being joined (AC10).
CONJUNCTIONS: dict[RoleField | str, tuple[str, str]] = {
    RoleField.TENSION: ("Nhưng", "Có điều,"),
    "step": ("Vì vậy,", "Từ đó,"),
    RoleField.RESOURCE: ("Vì vậy,", "Từ đó,"),
    RoleField.CORE: ("Bên cạnh đó,", "Thêm nữa,"),
    RoleField.OPTION: ("Bên cạnh đó,", "Thêm nữa,"),
}
ALL_CONJUNCTIONS = frozenset(c for pair in CONJUNCTIONS.values() for c in pair)


@dataclass(frozen=True)
class PositionView:
    """What stance, summary and headline read from one rendered position."""

    key: str
    label: str
    card_id: str
    title: str
    core: str
    tension: str
    resource: str


def anchor(view: PositionView) -> str:
    """The role field a summary or a reason must mention for this position."""

    role = ROLES[view.key]
    if role.step or role.field is RoleField.RESOURCE:
        return view.resource if view.key != "focus" else view.core
    if role.field is RoleField.TENSION:
        return view.tension
    return view.core


def _role_sentence(view: PositionView) -> str:
    role = ROLES[view.key]
    if view.key == "focus" or role.field in {RoleField.CORE}:
        return f"{view.title} cho thấy {view.core}"
    if role.field is RoleField.TENSION:
        return f"{view.title} nhắc rằng bạn dễ {view.tension}"
    if role.field is RoleField.OPTION:
        # Two short sentences: a gain and its cost in one would exceed the density limit. With
        # the longest fields (core 19 words, three-word titles and conjunctions) each stays
        # within the review's 28-word sentence limit.
        return f"{view.title}: hướng này được {view.core}. Đổi lại, hướng này dễ {view.tension}"
    return f"{view.title} gợi ý bạn có thể {view.resource}"


def linked_summary(
    views: Sequence[PositionView], lead: Sequence[str] = (), reserve: int = 0
) -> str:
    """One sentence per role in spread order, joined by role-appropriate conjunctions.

    ``reserve`` words stay free for text added in front later (the B2-1 readiness line)."""

    sentences: list[str] = []
    for index, view in enumerate(views):
        body = _role_sentence(view)
        if index == 0:
            sentences.append(f"{body[:1].upper()}{body[1:]}.")
            continue
        role = ROLES[view.key]
        kind: RoleField | str = "step" if role.step else role.field
        conjunction = CONJUNCTIONS[kind][index % 2]
        sentences.append(f"{conjunction} {body}.")
    core = " ".join(sentences)
    extra = [line for line in lead if len(f"{line} {core}".split()) + reserve <= 180]
    return " ".join([*extra[:1], core])


def summary_links(summary: str, views: Sequence[PositionView]) -> bool:
    """Gate summary_links_cards: every role's anchor is present, with at least N-1 links."""

    if any(anchor(view) not in summary for view in views):
        return False
    links = sum(
        len(re.findall(rf"(?:^|[.!?]\s+){re.escape(c)}(?=\s)", summary)) for c in ALL_CONJUNCTIONS
    )
    return links >= len(views) - 1


def split_choice(question: str) -> tuple[TarotAction, TarotAction] | None:
    """A/B as two different closed action labels, or None when they cannot be told apart."""

    text = question_frame.fold(question)
    match = re.search(r"(?<!\w)giữa (.+?) và (.+?)(?:,|\?|$)", text)
    if match:
        left, right = match.group(1), match.group(2)
    elif " hay " in text:
        left, _, right = text.partition(" hay ")
        right = re.split(r"[,?]", right, maxsplit=1)[0]
    else:
        return None
    a, b = question_frame.match_action(left), question_frame.match_action(right)
    if a is None or b is None or a == b:
        return None
    return a, b


def _reason(view: PositionView) -> TarotStanceReason:
    role = ROLES[view.key]
    if role.field is RoleField.TENSION:
        text = f"{view.label}: {view.title} nhắc rằng bạn dễ {view.tension}."
    elif role.step or role.field is RoleField.RESOURCE:
        text = f"{view.label}: {view.title} gợi ý bạn có thể {view.resource}."
    else:
        text = f"{view.label}: {view.title} cho thấy {view.core}."
    return TarotStanceReason(position_key=view.key, card_id=view.card_id, text=text)


def stance_for(
    form: TarotQuestionForm,
    action: TarotAction | None,
    question: str,
    topic: TarotContext,
    views: Sequence[PositionView],
) -> TarotStance | None:
    """Lean for yes/no questions and separable choices (AC08, AC09); None for other forms."""

    if form is TarotQuestionForm.YES_NO:
        return yes_no_stance(action, topic, views)
    if form is TarotQuestionForm.CHOICE:
        return choice_stance(split_choice(question), topic, views)
    return None


def yes_no_stance(
    action: TarotAction | None, topic: TarotContext, views: Sequence[PositionView]
) -> TarotStance:
    contributions = [
        (role_weight(view.key) * _VALUE[lean_of(view.card_id, topic)], view) for view in views
    ]
    score = sum(value for value, _ in contributions)
    level = (
        TarotStanceLevel.LEAN_TRY
        if score >= 1
        else TarotStanceLevel.CONSIDER
        if score <= -1
        else TarotStanceLevel.UNCLEAR
    )
    if level is TarotStanceLevel.UNCLEAR:
        pro = [c for c in contributions if c[0] > 0]
        con = [c for c in contributions if c[0] < 0]
        picked = [max(pro, key=lambda c: c[0])] if pro else []
        picked += [min(con, key=lambda c: c[0])] if con else []
        if not picked:
            picked = contributions[:1]
    else:
        sign = 1 if level is TarotStanceLevel.LEAN_TRY else -1
        aligned = sorted((c for c in contributions if c[0] * sign > 0), key=lambda c: -abs(c[0]))
        picked = aligned[:2]
    phrase = ACTION_PHRASES.get(action, GENERIC_ACTION) if action else GENERIC_ACTION
    return TarotStance(
        version=STANCE_VERSION,
        kind=TarotStanceKind.YES_NO,
        topic=topic,
        level=level,
        action=action,
        conclusion=CONCLUSIONS[level].format(action=phrase),
        reasons=tuple(_reason(view) for _, view in picked[:2]),
    )


def choice_stance(
    options: tuple[TarotAction, TarotAction] | None,
    topic: TarotContext,
    views: Sequence[PositionView],
) -> TarotStance:
    by_key = {view.key: view for view in views}
    a_view, b_view = by_key.get("option_a"), by_key.get("option_b")
    if options is None or a_view is None or b_view is None:
        step = next((v for v in views if ROLES[v.key].step), views[-1])
        return TarotStance(
            version=STANCE_VERSION,
            kind=TarotStanceKind.CHOICE,
            topic=topic,
            level=TarotStanceLevel.CLARIFY_CHOICE,
            options=options,
            conclusion=CONCLUSIONS[TarotStanceLevel.CLARIFY_CHOICE],
            reasons=(_reason(step),),
        )
    a_value = _VALUE[lean_of(a_view.card_id, topic)]
    b_value = _VALUE[lean_of(b_view.card_id, topic)]
    if a_value == b_value:
        level, chosen = TarotStanceLevel.UNCLEAR, None
    else:
        level = TarotStanceLevel.LEAN_TRY
        chosen = options[0] if a_value > b_value else options[1]
    return TarotStance(
        version=STANCE_VERSION,
        kind=TarotStanceKind.CHOICE,
        topic=topic,
        level=level,
        action=chosen,
        options=options,
        conclusion=CONCLUSIONS[level].format(action=ACTION_PHRASES[chosen] if chosen else ""),
        reasons=(_reason(a_view), _reason(b_view)),
    )


def recompute(stance: TarotStance, views: Sequence[PositionView]) -> TarotStance:
    """The stance the cards give for this stance's kind, action and options (stance_consistent)."""

    if stance.kind is TarotStanceKind.YES_NO:
        return yes_no_stance(stance.action, stance.topic, views)
    return choice_stance(stance.options, stance.topic, views)


def dynamic_headline(
    form: TarotQuestionForm,
    stance: TarotStance | None,
    action: TarotAction | None,
    topic: TarotContext,
    focal: PositionView,
    second: PositionView | None,
) -> str:
    """Headline from form + lean (or action/topic) + the focal card (AC11).

    ``second`` (the pitfall card, else another card) joins how/why/open/clarify headlines, so two
    readings share a headline only when they share both cards, the form and the topic.
    """

    chosen = stance.action if stance is not None else action
    phrase = ACTION_PHRASES[chosen] if chosen else GENERIC_ACTION
    key = stance.level.value if stance is not None else form.value
    template = HEADLINES.get(key, HEADLINES[TarotQuestionForm.OPEN.value])
    pair = f"{focal.title} và {second.title}" if second is not None else focal.title
    target = phrase if chosen else f"cho {TOPIC_PHRASES[topic]}"
    return template.format(
        focal=focal.title, pair=pair, action=phrase, topic=TOPIC_PHRASES[topic], target=target
    )
