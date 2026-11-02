"""Lean, linked summary and dynamic headline for framed Tarot readings (US-20 AC08-AC11, B2-3).

Everything here is authored copy or a deterministic rule over closed labels; nothing is taken
from the question's text. New copy needs owner approval before release, and this module joins
the fallback approval scope then (docs/plans/2026-10-18-b2-3-tarot-stance-task.md).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from app.domains.tarot import phrasing, question_frame
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

# v2 (2026-10-19): self-care and boundary actions never get "consider more before" (see
# SELF_CARE_ACTIONS). Stored v1 stances keep their recorded version.
STANCE_VERSION = "tarot-stance-v2"


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
# Roast conclusions carry the same marker as the direct ones (AC19).
ROAST_CONCLUSIONS: dict[TarotStanceLevel, str] = {
    TarotStanceLevel.LEAN_TRY: (
        "Các lá bật đèn xanh nhẹ: nghiêng về thử {action}, chưa phải lệnh đâu."
    ),
    TarotStanceLevel.CONSIDER: "Khoan đạp ga: cân nhắc thêm trước khi {action} nha.",
    TarotStanceLevel.UNCLEAR: "Chưa rõ: các lá kéo về hai phía, hội đồng chưa thống nhất.",
    TarotStanceLevel.CLARIFY_CHOICE: (
        "Trải này chưa so được hai hướng; xem điều cần rõ trước khi chọn đã nha."
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
# Headline = form + lean (or action/topic) (AC11 as changed by the owner, 29/10/2026: no card
# names, so a headline never names two of five cards as if they were the reading). Three frames
# per key, picked once per session (AC15). Frame i of ROAST_HEADLINES is the Roast version of
# frame i ("headline.<key>.<i>", AC19). Stance headlines keep their level's marker; timing
# headlines all say "sẵn sàng" (AC05). No headline gives advice (content standard psychology
# checklist, US-20 AC14): the stance marker states the lean, nothing tells the reader what to do.
# Worst case (a 6-word action, a 3-word topic) stays within the 18-word headline budget; tests
# check every frame.
HEADLINES: dict[str, tuple[str, str, str]] = {
    TarotStanceLevel.LEAN_TRY.value: (
        "Các lá nghiêng về thử {action}.",
        "Với chuyện này, các lá nghiêng về thử {action}.",
        "Lúc này, các lá nghiêng về thử {action}.",
    ),
    TarotStanceLevel.CONSIDER.value: (
        "Các lá gợi ý cân nhắc thêm trước khi {action}.",
        "Lúc này, cân nhắc thêm trước khi {action}.",
        "Chuyện này cần cân nhắc thêm trước khi {action}.",
    ),
    TarotStanceLevel.UNCLEAR.value: (
        "Chuyện {action} còn kéo về hai phía.",
        "Với chuyện {action}, các lá kéo về hai phía.",
        "Các lá cho thấy chuyện {action} kéo về hai phía.",
    ),
    TarotStanceLevel.CLARIFY_CHOICE.value: (
        "Có điều cần rõ trước khi chọn.",
        "Hai hướng đều có giá, có điều cần rõ trước khi chọn.",
        "Các lá chỉ ra điều cần rõ trước khi chọn.",
    ),
    TarotQuestionForm.TIMING.value: (
        "Điều cần sẵn sàng trước khi {action}.",
        "Lúc này, cần sẵn sàng điều này trước khi {action}.",
        "Các lá chỉ ra điều cần sẵn sàng trước khi {action}.",
    ),
    TarotQuestionForm.HOW.value: (
        "Một cách bắt đầu {target}.",
        "Bắt đầu {target} từ một việc nhỏ.",
        "Các lá gợi ý cách bắt đầu {target}.",
    ),
    TarotQuestionForm.WHY.value: (
        "Một lý do đáng nhìn trong {topic}.",
        "Trong {topic}, có một lý do đáng nhìn.",
        "Các lá gợi một lý do trong {topic}.",
    ),
    TarotQuestionForm.OPEN.value: (
        "Lúc này, điều đáng nhìn rõ trong {topic}.",
        "Trong {topic}, có một điều đáng nhìn rõ.",
        "Các lá chỉ ra điều đáng nhìn trong {topic}.",
    ),
}
ROAST_HEADLINES: dict[str, tuple[str, str, str]] = {
    TarotStanceLevel.LEAN_TRY.value: (
        "Đèn xanh nhẹ: nghiêng về thử {action}.",
        "Các lá nháy mắt: nghiêng về thử {action}.",
        "Nghiêng về thử {action}, nhẹ nhàng thôi.",
    ),
    TarotStanceLevel.CONSIDER.value: (
        "Kéo phanh tay: cân nhắc thêm trước khi {action}.",
        "Đèn vàng: cân nhắc thêm trước khi {action}.",
        "Chậm lại chút: cân nhắc thêm trước khi {action}.",
    ),
    TarotStanceLevel.UNCLEAR.value: (
        "Hội đồng đang giằng co: chuyện {action} kéo về hai phía.",
        "Chia phe rồi: chuyện {action} kéo về hai phía.",
        "Chuyện {action} kéo về hai phía, chưa ai chịu chốt.",
    ),
    TarotStanceLevel.CLARIFY_CHOICE.value: (
        "Còn giằng co: có điều cần rõ trước khi chọn.",
        "Chưa so kèo được: có điều cần rõ trước khi chọn.",
        "Điều cần rõ trước khi chọn nằm ngay dưới đây.",
    ),
    TarotQuestionForm.TIMING.value: (
        "Khỏi xem lịch: sẵn sàng điều này trước khi {action}.",
        "Lo phần sẵn sàng trước khi {action}.",
        "Khỏi đồng hồ: sẵn sàng điều này trước khi {action}.",
    ),
    TarotQuestionForm.HOW.value: (
        "Khỏi lý thuyết: một cách bắt đầu {target}.",
        "Cẩm nang gọn: bắt đầu {target}.",
        "Chỉ đường gọn: bắt đầu {target}.",
    ),
    TarotQuestionForm.WHY.value: (
        "Truy tới gốc một lý do trong {topic}.",
        "Lật lại một lý do trong {topic}.",
        "Soi tới gốc một lý do trong {topic}.",
    ),
    TarotQuestionForm.OPEN.value: (
        "Nói gọn về {topic} nè.",
        "Soi nhanh {topic}, khỏi vòng vo.",
        "Gom lại vài ý chính về {topic} nè.",
    ),
}


@dataclass(frozen=True)
class PositionView:
    """What stance, summary and headline read from one rendered position."""

    key: str
    label: str
    card_id: str
    title: str
    core: str
    # The core as a complete clause (phrasing.core_sentence, Tarot pass 2): what framed prose
    # quotes. ``core`` stays the authored field.
    core_sentence: str
    tension: str
    resource: str


def anchor(view: PositionView) -> str:
    """The role field a summary or a reason must mention for this position (the core as a
    clause since Tarot pass 2)."""

    role = ROLES[view.key]
    if role.step or role.field is RoleField.RESOURCE:
        return view.resource if view.key != "focus" else view.core_sentence
    if role.field is RoleField.TENSION:
        return view.tension
    return view.core_sentence


SUMMARY_BUDGET = 180  # words; the engine's scan budget
OPTION_NAMES = {"option_a": "A", "option_b": "B"}


def summary_views(views: Sequence[PositionView]) -> list[PositionView]:
    """The roles the summary speaks for (owner, 29/10/2026): the first card that shows what is
    already there, then both options of a choice (each with its cost) or else the first pitfall.
    Other roles stay in their own position block below, so the summary does not repeat the
    whole reading."""

    chosen: list[PositionView] = []
    core = next(
        (v for v in views if v.key == "focus" or ROLES[v.key].field is RoleField.CORE), None
    )
    if core is not None:
        chosen.append(core)
    options = [v for v in views if ROLES[v.key].field is RoleField.OPTION]
    chosen.extend(options)
    tension = next((v for v in views if ROLES[v.key].field is RoleField.TENSION), None)
    if tension is not None and not options:
        chosen.append(tension)
    return chosen


def _plain_sentence(view: PositionView) -> str:
    """No card is the subject; card names stay in the position blocks. The core is a complete
    clause (Tarot pass 2), so it stands as its own sentence without a "Điểm chính:" label."""

    role = ROLES[view.key]
    if role.field is RoleField.OPTION:
        name = OPTION_NAMES.get(view.key, "này")
        return f"Với hướng {name}, {view.core_sentence}. Đổi lại, bạn dễ {view.tension}."
    if role.field is RoleField.TENSION:
        return f"Có điều, bạn dễ {view.tension}."
    return f"{phrasing.capitalized(view.core_sentence)}."


def step_sentence(step: str) -> str:
    """The summary's last sentence; a step that ends on a quoted line keeps its own stop."""

    return f"Trước hết, {step}" if step.endswith(("”", "?", "!")) else f"Trước hết, {step}."


def plain_summary(
    views: Sequence[PositionView],
    step: str | None,
    lead: Sequence[str] = (),
    reserve: int = 0,
) -> str:
    """What the reading says in a few plain sentences, ending on the one step the reader sees at
    the step position (``step`` is that position's action without its lead-in).

    No card names and no linking words between unrelated cards (owner feedback, 29/10/2026, on
    "Ngôi Sao cho thấy… Có điều nè, Át Kiếm nhắc… Thêm nữa nè…"). ``reserve`` words stay free for
    text added in front later (the B2-1 readiness line)."""

    sentences = [_plain_sentence(view) for view in summary_views(views)]
    if step:
        sentences.append(step_sentence(step))
    core = " ".join(sentences)
    extra = [line for line in lead if len(f"{line} {core}".split()) + reserve <= SUMMARY_BUDGET]
    return " ".join([*extra[:1], core])


def _folded(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def summary_covers(
    summary: str,
    views: Sequence[PositionView],
    step: str | None,
    card_titles: Sequence[str] = (),
) -> bool:
    """Gate summary_plain (gates v6, replaces summary_links_cards): the summary carries each
    summarized role's anchor, ends on exactly the shown step, and names no card of the closed
    catalog (``card_titles``, both languages; NFC + case-insensitive), selected or not.

    The authored anchors and step are removed before the title scan, so a card field that happens
    to contain a title's words (for example "tiếng gọi") cannot trip it (Codex r54)."""

    for view in summary_views(views):
        role = ROLES[view.key]
        needed = (
            (view.core_sentence, view.tension)
            if role.field is RoleField.OPTION
            else (anchor(view),)
        )
        # The core clause may open a sentence, so its first letter may be capitalized.
        if any(not phrasing.contains_clause(summary, text) for text in needed):
            return False
    if step and not summary.endswith(step_sentence(step)):
        return False
    rest = summary
    authored = [step or ""]
    for view in summary_views(views):
        for text in (view.core, view.core_sentence, view.tension, anchor(view)):
            authored.extend((text, phrasing.capitalized(text)))
    for text in sorted({t for t in authored if t}, key=len, reverse=True):
        rest = rest.replace(text, " ")
    folded = _folded(rest)
    titles = {*card_titles, *(view.title for view in views)}
    return not any(
        re.search(rf"(?<!\w){re.escape(_folded(title))}(?!\w)", folded) for title in titles
    )


_ALTERNATIVE_SEPARATORS = re.compile(r"(?<!\w)(?:hay|hoặc|hay là)(?!\w)")


_AND = re.compile(r"(?<!\w)và(?!\w)")
# A clause after a comma that opens with one of these adds another alternative.
_CONTINUATION = re.compile(r"^\s*(?:và|hay|hoặc|hay là|cả)(?!\w)")


def split_choice(
    question: str, *, asked_clause: bool = False
) -> tuple[TarotAction, TarotAction] | None:
    """A/B as two different closed action labels, only for an unambiguous two-option shape.

    The shape is checked over the whole question, not just up to the first comma:
    - "Giữa A và B, ...": exactly one "và" in the question and no "hay"/"hoặc";
    - "Nên A hay B?": exactly one "hay"/"hoặc" in the question;
    - in both, no later clause may open with "và"/"hay"/"hoặc" ("Giữa A và B, và C, ...").
    Anything else is not an A/B question: the reading then shows what to clarify before
    choosing (US-20 AC08).
    """

    text = question_frame.fold(question)
    clauses = re.split(r"[,;?]", text)
    if any(_CONTINUATION.search(clause) for clause in clauses[1:]):
        return None
    between = re.search(r"(?<!\w)giữa (.+?)(?:,|;|\?|$)", text)
    if between:
        parts = _AND.split(between.group(1))
        if len(parts) != 2 or len(_AND.findall(text)) != 1 or _ALTERNATIVE_SEPARATORS.search(text):
            return None
        left, right = parts
    else:
        parts = _ALTERNATIVE_SEPARATORS.split(clauses[0])
        if len(parts) != 2 or len(_ALTERNATIVE_SEPARATORS.findall(text)) != 1:
            return None
        left, right = parts
    if asked_clause:
        # Frame v2 (T01): a background clause inside an option is not that option's action.
        left, right = question_frame.target_clause(left), question_frame.target_clause(right)
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
        text = f"{view.label}: {view.title} cho thấy {view.core_sentence}."
    return TarotStanceReason(position_key=view.key, card_id=view.card_id, text=text)


def stance_for(
    form: TarotQuestionForm,
    action: TarotAction | None,
    question: str,
    topic: TarotContext,
    views: Sequence[PositionView],
    *,
    roast: bool = False,
    asked_clause: bool = False,
) -> TarotStance | None:
    """Lean for yes/no questions and separable choices (AC08, AC09); None for other forms.

    ``roast`` picks the Roast conclusion (AC19); level, action, options and reasons are the same.
    """

    if form is TarotQuestionForm.YES_NO:
        return yes_no_stance(action, topic, views, roast=roast)
    if form is TarotQuestionForm.CHOICE:
        return choice_stance(
            split_choice(question, asked_clause=asked_clause), topic, views, roast=roast
        )
    return None


# Self-care and boundary actions (owner decision 2026-10-19). A "hold" card must not turn into
# "consider more before resting / stopping / saying no / asking for help": that contradicts the
# step the same reading offers and the content standard (never discourage self-care). For these
# actions a hold card counts as neutral, so the lean is "try" or "unclear", never "consider".
SELF_CARE_ACTIONS = frozenset(
    {
        TarotAction.NGHI_NGOI,
        TarotAction.DUNG_LAI,
        TarotAction.TU_CHOI,
        TarotAction.DAT_RANH_GIOI,
        TarotAction.NHO_GIUP,
        TarotAction.TU_THUONG,
    }
)


def yes_no_stance(
    action: TarotAction | None,
    topic: TarotContext,
    views: Sequence[PositionView],
    *,
    roast: bool = False,
) -> TarotStance:
    contributions = [
        (role_weight(view.key) * _VALUE[lean_of(view.card_id, topic)], view) for view in views
    ]
    if action in SELF_CARE_ACTIONS:
        contributions = [(max(value, 0.0), view) for value, view in contributions]
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
        conclusion=(ROAST_CONCLUSIONS if roast else CONCLUSIONS)[level].format(action=phrase),
        reasons=tuple(_reason(view) for _, view in picked[:2]),
    )


def choice_stance(
    options: tuple[TarotAction, TarotAction] | None,
    topic: TarotContext,
    views: Sequence[PositionView],
    *,
    roast: bool = False,
) -> TarotStance:
    conclusions = ROAST_CONCLUSIONS if roast else CONCLUSIONS
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
            conclusion=conclusions[TarotStanceLevel.CLARIFY_CHOICE],
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
        conclusion=conclusions[level].format(action=ACTION_PHRASES[chosen] if chosen else ""),
        reasons=(_reason(a_view), _reason(b_view)),
    )


def recompute(
    stance: TarotStance, views: Sequence[PositionView], *, roast: bool = False
) -> TarotStance:
    """The stance the cards give for this stance's kind, action and options (stance_consistent)."""

    if stance.kind is TarotStanceKind.YES_NO:
        return yes_no_stance(stance.action, stance.topic, views, roast=roast)
    return choice_stance(stance.options, stance.topic, views, roast=roast)


def dynamic_headline(
    form: TarotQuestionForm,
    stance: TarotStance | None,
    action: TarotAction | None,
    topic: TarotContext,
    *,
    variant: int = 0,
    roast: bool = False,
) -> str:
    """Headline from form + lean (or action/topic) (AC11; no card names since the owner's
    feedback of 29/10/2026), in frame ``variant`` of the voice register (AC15, AC19)."""

    chosen = stance.action if stance is not None else action
    phrase = ACTION_PHRASES[chosen] if chosen else GENERIC_ACTION
    key = stance.level.value if stance is not None else form.value
    table = ROAST_HEADLINES if roast else HEADLINES
    frames = table.get(key, table[TarotQuestionForm.OPEN.value])
    template = frames[variant % len(frames)]
    target = phrase if chosen else f"cho {TOPIC_PHRASES[topic]}"
    return template.format(action=phrase, topic=TOPIC_PHRASES[topic], target=target)
