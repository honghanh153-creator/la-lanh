"""Role-based meaning for each Tarot position (US-20 AC07/AC12 B2-2; AC15/AC16/AC19 B2-4).

Each spread position has one role. The role picks which authored card field is read there
(core, tension or resource) and the sentence frame around it, and whether the position carries
the reading's small action. Only step roles carry an action. Frames hold no "Ý chính của lá",
"Thử nhé:" or "Ví dụ:" prefixes. Used for sessions that have a stored QuestionFrame (B2-1 and
later); earlier sessions keep the legacy renderer. Since B2-4 each role has three frames per
voice register, picked once per session (tarot/variants.py), and every position starts with a
lead chosen by the question's form, so two questions over the same card and role read
differently (US-20 AC16).

New copy in this module needs owner approval before release, and the module joins the fallback
approval scope at that point (docs/plans/2026-10-17-b2-2-tarot-roles-task.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.domains.tarot.models import TarotQuestionForm

ROLE_COPY_VERSION = "tarot-roles-v3"  # v3: Tarot pass 2, no header labels (29/10/2026)
FRAME_VARIANTS = 3  # role frames per voice register (US-20 AC15)
LEAD_VARIANTS = 5  # one lead per position of the longest spread, never repeated in a reading


class RoleField(StrEnum):
    CORE = "core"  # what the card shows as already there
    TENSION = "tension"  # the pitfall or what is easy to miss
    RESOURCE = "resource"  # what the reader can do
    OPTION = "option"  # an option's gain (core) and its cost (tension)


@dataclass(frozen=True)
class PositionRole:
    field: RoleField
    # Direct-voice frames around the field ({core_sentence} {tension} {resource}). Frame i of
    # ``roast`` is the Roast version of frame i: both carry the code "<position_key>.<i>" (AC19).
    frames: tuple[str, str, str]
    roast: tuple[str, str, str]
    step: bool = False  # only step roles carry the reading's small action


# Word budget per sentence (the review's 28-word density limit) with a lead of at most 4 words
# and the longest card fields (core sentence 18, tension 16, resource 17 words): frame words in
# the sentence around the field stay <= 6 for the core sentence, <= 8 for tension and <= 7 for
# resource. Option roles and the one-card focus use two sentences; the lead joins the first.
# Tests check every frame x the longest lead x card x topic.
#
# Tarot pass 2 (owner, 29/10/2026): frames no longer restate the position header as a label
# ("Bằng chứng thật: …", "Kịch bản tự viết: …"). Core roles read the card's core as a complete
# clause ({core_sentence}, phrasing.core_sentence); tension roles say "có thể bạn đang …";
# resource roles say "bạn có thể …"; option roles name the gain and the cost. Roast keeps a
# playful tag instead of a label. Slots and codes "<key>.<i>" are unchanged (AC19).
# Keyed by the position keys of engine._POSITIONS.
ROLES: dict[str, PositionRole] = {
    # One card: what to look at, then what is in reach; it is also the step.
    "focus": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}. Bạn có thể bắt đầu bằng việc {resource}.",
            "Có thể thấy {core_sentence}. Việc trong tầm tay bạn là {resource}.",
            "Có vẻ {core_sentence}. Một bước nhỏ bạn làm được là {resource}.",
        ),
        (
            "{core_sentence}, nói thẳng vậy đó. Khỏi chờ ai, bạn có thể {resource}.",
            "{core_sentence}, khỏi vòng vo. Phần bạn tự lo được là {resource}.",
            "Nói gọn thì {core_sentence}. Việc làm được ngay là {resource}.",
        ),
        step=True,
    ),
    # Three cards.
    "clear": PositionRole(
        RoleField.CORE,
        ("{core_sentence}.", "Có thể thấy {core_sentence}.", "{core_sentence}, điều này khá rõ."),
        (
            "{core_sentence}, rõ như ban ngày.",
            "{core_sentence}, khỏi đoán nữa.",
            "{core_sentence}, rõ mười mươi rồi.",
        ),
    ),
    "missed": PositionRole(
        RoleField.TENSION,
        (
            "Có thể bạn chưa để ý mình đang {tension}.",
            "Có lúc bạn {tension} mà không nhận ra.",
            "Bạn có thể đang {tension}.",
        ),
        (
            "Có khi bạn đang {tension} mà không hay biết.",
            "Không chừng bạn đang {tension}, nghe quen không?",
            "Lỡ đâu bạn đang {tension} mà chưa nhận ra.",
        ),
    ),
    "next": PositionRole(
        RoleField.RESOURCE,
        (
            "{core_sentence}, đó là điểm tựa.",
            "Nhớ rằng {core_sentence}.",
            "Mang theo điều này: {core_sentence}.",
        ),
        (
            "{core_sentence}, nhớ mang theo nha.",
            "{core_sentence}, nhớ kỹ trước khi lao.",
            "{core_sentence}, bỏ túi nha.",
        ),
        step=True,
    ),
    # Five cards: clarity.
    "facts": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}.",
            "Điều có thể dựa vào là {core_sentence}.",
            "Có một điều khá chắc: {core_sentence}.",
        ),
        (
            "{core_sentence}, cái này có thật nha.",
            "{core_sentence}, không phải phim đâu.",
            "{core_sentence}, chắc tay đó.",
        ),
    ),
    "assumption": PositionRole(
        RoleField.TENSION,
        (
            "Có thể bạn đang {tension}. Phần này chưa phải dữ kiện.",
            "Bạn có thể đang {tension} mà chưa kiểm tra.",
            "Có lúc bạn {tension}, dù chưa có gì chắc.",
        ),
        (
            "Không chừng bạn đang {tension}. Phần này chưa phải dữ kiện đâu.",
            "Có khi bạn đang {tension}, rồi tin luôn.",
            "Lỡ đâu bạn đang {tension} mà chưa kiểm chứng.",
        ),
    ),
    "need": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}.",
            "{core_sentence}, điều này đáng được giữ.",
            "Thật ra {core_sentence}.",
        ),
        (
            "{core_sentence}, nói thật lòng đó.",
            "{core_sentence}, nhu cầu chính chủ đó.",
            "Thật ra {core_sentence}, khỏi chối.",
        ),
    ),
    "agency": PositionRole(
        RoleField.RESOURCE,
        (
            "Bạn có thể {resource}.",
            "Việc bạn tự làm được là {resource}.",
            "Bạn không cần chờ ai để {resource}.",
        ),
        (
            "Việc bạn tự xử được là {resource}.",
            "Khỏi chờ ai mới được {resource}.",
            "{resource}, nút này bạn tự bấm được.",
        ),
    ),
    # Five cards: loop.
    "trigger": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}.",
            "Chuyện thường bắt đầu khi {core_sentence}.",
            "Hay có cảnh này: {core_sentence}.",
        ),
        (
            "{core_sentence}, ngòi nổ quen mặt đó.",
            "{core_sentence}, cảnh mở màn quen thuộc.",
            "Chuyện hay nổ ra khi {core_sentence}.",
        ),
    ),
    "habit": PositionRole(
        RoleField.TENSION,
        (
            "Thói quen khiến bạn dễ {tension}.",
            "Bạn hay {tension} mà chưa kịp nghĩ.",
            "Hễ gặp chuyện là bạn dễ {tension}.",
        ),
        (
            "Bạn dễ {tension}, như được cài sẵn.",
            "Bạn lại {tension}, y như phim cũ.",
            "Phản xạ tủ của bạn là {tension}.",
        ),
    ),
    "payoff": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}.",
            "Phản xạ ấy giúp được vì {core_sentence}.",
            "Nó còn đó vì {core_sentence}.",
        ),
        (
            "{core_sentence}, thế nên nó bám dai.",
            "Nó cứu bạn lúc đó vì {core_sentence}.",
            "Lợi trước mắt là {core_sentence}.",
        ),
    ),
    "cost": PositionRole(
        RoleField.TENSION,
        (
            "Nếu cứ như cũ, về sau bạn dễ {tension}.",
            "Để lâu thì bạn dễ {tension}.",
            "Giữ mãi cách này thì bạn dễ {tension}.",
        ),
        (
            "Cứ thế mãi thì bạn dễ {tension}.",
            "Kéo dài kiểu này thì bạn dễ {tension}.",
            "Phí ẩn ở đây là bạn dễ {tension}.",
        ),
    ),
    "alternative": PositionRole(
        RoleField.RESOURCE,
        (
            "{core_sentence}, đó là nền cho cách mới.",
            "Cách mới dựa vào chỗ {core_sentence}.",
            "Muốn đổi cách, nhớ rằng {core_sentence}.",
        ),
        (
            "Đổi kịch bản thì nhớ rằng {core_sentence}.",
            "{core_sentence}, bản mới dựa vào đó.",
            "{core_sentence}, nhớ trước khi đổi vai.",
        ),
        step=True,
    ),
    # Five cards: choice.
    "option_a": PositionRole(
        RoleField.OPTION,
        (
            "Hướng này cho thấy {core_sentence}. Đổi lại, bạn dễ {tension}.",
            "Chọn hướng này thì {core_sentence}. Cái giá là bạn dễ {tension}.",
            "Theo hướng này thì {core_sentence}. Nhưng bạn cũng dễ {tension}.",
        ),
        (
            "Điểm cộng là {core_sentence}. Điểm trừ là bạn dễ {tension}.",
            "Món hời ở đây là {core_sentence}. Kèm theo đó, bạn dễ {tension}.",
            "Chọn hướng này thì {core_sentence}. Phí phải trả là bạn dễ {tension}.",
        ),
    ),
    "option_b": PositionRole(
        RoleField.OPTION,
        (
            "Hướng này cho thấy {core_sentence}. Đổi lại, bạn dễ {tension}.",
            "Chọn hướng này thì {core_sentence}. Cái giá là bạn dễ {tension}.",
            "Theo hướng này thì {core_sentence}. Nhưng bạn cũng dễ {tension}.",
        ),
        (
            "Điểm cộng là {core_sentence}. Điểm trừ là bạn dễ {tension}.",
            "Món hời ở đây là {core_sentence}. Kèm theo đó, bạn dễ {tension}.",
            "Chọn hướng này thì {core_sentence}. Phí phải trả là bạn dễ {tension}.",
        ),
    ),
    "tradeoff": PositionRole(
        RoleField.TENSION,
        (
            "Chỗ khó là bạn dễ {tension}.",
            "Cán cân dễ lệch khi bạn {tension}.",
            "Bạn dễ {tension} khi so hai bên.",
        ),
        (
            "Chỗ kẹt là bạn dễ {tension}.",
            "Bàn cân dễ lệch khi bạn {tension}.",
            "Cân tới cân lui thì bạn dễ {tension}.",
        ),
    ),
    "criterion": PositionRole(
        RoleField.RESOURCE,
        (
            "Bạn có thể tự chốt bằng cách {resource}.",
            "Một cách tự chốt là {resource}.",
            "Thước đo riêng của bạn là {resource}.",
        ),
        (
            "Bài test nhỏ để chốt là {resource}.",
            "Thước đo tự chế là {resource}.",
            "Muốn chốt thì cứ {resource}.",
        ),
        step=True,
    ),
    # Five cards: conversation.
    "feeling": PositionRole(
        RoleField.CORE,
        (
            "{core_sentence}.",
            "Cảm xúc này đến từ chỗ {core_sentence}.",
            "Điều nằm dưới cảm xúc là {core_sentence}.",
        ),
        (
            "{core_sentence}, tim đang nói vậy đó.",
            "Cảm xúc đang gõ cửa vì {core_sentence}.",
            "Dưới lớp cảm xúc là chỗ {core_sentence}.",
        ),
    ),
    "boundary": PositionRole(
        RoleField.RESOURCE,
        (
            "Một cách giữ ranh giới là {resource}.",
            "Ranh giới có thể là {resource}.",
            "Bạn giữ phần mình bằng cách {resource}.",
        ),
        (
            "Ranh giới gọn nhất là {resource}.",
            "Muốn giữ phần mình thì {resource}.",
            "Bạn hoàn toàn có thể {resource}.",
        ),
    ),
    "opening": PositionRole(
        RoleField.RESOURCE,
        (
            "Trước khi mở lời, nhớ rằng {core_sentence}.",
            "{core_sentence}, nhớ điều này khi mở lời.",
            "Câu mở đầu dựa vào chỗ {core_sentence}.",
        ),
        (
            "Trước khi gõ phím, nhớ rằng {core_sentence}.",
            "{core_sentence}, mở lời từ đó cho mượt.",
            "Câu chào sân dựa vào chỗ {core_sentence}.",
        ),
        step=True,
    ),
}

# Leads by question form (AC16): at most 4 words, shared by every voice, never text from the
# question. Position i of a reading uses lead (offset + i) mod 5, so no lead repeats in a reading.
LEADS: dict[TarotQuestionForm, tuple[str, str, str, str, str]] = {
    TarotQuestionForm.YES_NO: (
        "Để tự trả lời,",
        "Để tự quyết,",
        "Cân cả hai phía,",
        "Nếu đang phân vân,",
        "Với câu hỏi này,",
    ),
    TarotQuestionForm.CHOICE: (
        "Giữa hai lựa chọn,",
        "So hai hướng,",
        "Để chọn công bằng,",
        "Nhìn cả hai hướng,",
        "Trước ngã rẽ này,",
    ),
    TarotQuestionForm.HOW: (
        "Để tìm cách làm,",
        "Về cách làm,",
        "Để bắt đầu,",
        "Nếu muốn làm được,",
        "Để đi bước đầu,",
    ),
    TarotQuestionForm.WHY: (
        "Về lý do,",
        "Soi vào lý do,",
        "Để hiểu vì sao,",
        "Tìm gốc chuyện,",
        "Nhìn từ gốc,",
    ),
    TarotQuestionForm.TIMING: (
        "Để sẵn sàng hơn,",
        "Về độ sẵn sàng,",
        "Để chuẩn bị,",
        "Chưa cần ngày giờ,",
        "Để có đà,",
    ),
    TarotQuestionForm.OPEN: (
        "Nhìn chung,",
        "Ở chuyện này,",
        "Lúc này,",
        "Trong bức tranh chung,",
        "Từ góc này,",
    ),
}
LEAD_MAX_WORDS = 4
# Sentence the gentle_specific voice adds after a role reading.
GENTLE_CHECK = "Chưa cần kết luận ngay; hãy kiểm tra bằng chuyện thật trước."


def frame_code(position_key: str, index: int) -> str:
    """Combination code shared by a direct frame and its Roast version (AC19)."""

    return f"{position_key}.{index}"


# Gate no_decision_or_prediction (US-20 AC13): never choose for the reader or foretell.
DECISION_OR_PREDICTION = (
    r"\bbạn (?:nên|phải) chọn\b",
    r"\bhãy chọn (?:hướng|phương án) [ab]\b",
    r"\bquyết định đúng (?:là|nhất)\b",
    r"\b(?:chắc chắn|nhất định|rồi) sẽ\b",
    r"\bsẽ (?:thành công|thất bại|quay lại|xảy ra|đến với bạn)\b",
    r"\b(?:anh ấy|cô ấy|người ấy|họ) (?:sẽ|đang nghĩ|thật ra muốn)\b",
)

STEP_ROLES = frozenset(key for key, role in ROLES.items() if role.step)
# Prefixes AC12 removes from new readings.
RETIRED_PREFIXES = ("ý chính của lá", "ý chính:", "thử nhé:", "một việc nhỏ:", "ví dụ:")
_EXAMPLE_PREFIX = re.compile(r"^\s*ví dụ\s*:\s*", re.IGNORECASE)


def scene_without_label(scene: str) -> str:
    """The UI already titles the block "Ví dụ để đối chiếu"; drop a leading "Ví dụ:"."""

    rest = _EXAMPLE_PREFIX.sub("", scene, count=1)
    return rest[:1].upper() + rest[1:] if rest else scene


def lead_for(form: TarotQuestionForm, offset: int, position_index: int) -> str:
    return LEADS[form][(offset + position_index) % LEAD_VARIANTS]


def meaning_for(
    position_key: str,
    *,
    core_sentence: str,
    tension: str,
    resource: str,
    frame: int = 0,
    roast: bool = False,
    lead: str | None = None,
) -> str:
    """The role's sentence: frame ``frame`` of the voice register, after an optional lead.

    ``core_sentence`` is the card's core as a clause (phrasing.core_sentence); a frame that opens
    on a field gets its first letter capitalized, or lowered after a lead."""

    role = ROLES[position_key]
    template = (role.roast if roast else role.frames)[frame % FRAME_VARIANTS]
    text = template.format(core_sentence=core_sentence, tension=tension, resource=resource)
    if lead is None:
        return f"{text[:1].upper()}{text[1:]}"
    return f"{lead} {text[:1].lower()}{text[1:]}"


def action_for(resource: str) -> str:
    """A step role's small action from the card's resource, without a "Thử nhé:" prefix."""

    step = resource.partition(", rồi ")[0]
    return f"{step[:1].upper()}{step[1:]}."
