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

ROLE_COPY_VERSION = "tarot-roles-v2"
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
    # Direct-voice frames around the field ({core} {tension} {resource}). Frame i of ``roast``
    # is the Roast version of frame i: both carry the code "<position_key>.<i>" (AC19).
    frames: tuple[str, str, str]
    roast: tuple[str, str, str]
    step: bool = False  # only step roles carry the reading's small action


# Word budget per sentence (the review's 28-word density limit) with a lead of at most 4 words
# and the longest card fields (core 19, tension 16, resource 17 words): frame words before or
# around the field stay <= 5 for core, <= 8 for tension and <= 7 for resource. Option roles and
# the one-card focus use two sentences; the lead joins the first. audit_frame_lengths checks
# every frame x lead x card x topic.
# Keyed by the position keys of engine._POSITIONS.
ROLES: dict[str, PositionRole] = {
    # One card: what to look at, then what is in reach; it is also the step.
    "focus": PositionRole(
        RoleField.CORE,
        (
            "Lá này cho thấy {core}. Phần nằm trong tay bạn: {resource}.",
            "Điều lá này chỉ ra: {core}. Việc bạn làm được: {resource}.",
            "Điểm đáng nhìn ở đây: {core}. Bước trong tầm tay: {resource}.",
        ),
        (
            "Lá này bóc trần: {core}. Phần bạn tự lo được: {resource}.",
            "Nói gọn cho bạn: {core}. Việc làm được ngay: {resource}.",
            "Lá này nói thẳng: {core}. Khỏi chờ ai, bạn có thể {resource}.",
        ),
        step=True,
    ),
    # Three cards.
    "clear": PositionRole(
        RoleField.CORE,
        ("Lá này cho thấy {core}.", "Điều đã khá rõ: {core}.", "Phần đang có sẵn: {core}."),
        (
            "Rõ như ban ngày: {core}.",
            "Khỏi đoán, lá này nói: {core}.",
            "Chuyện đã rõ mười mươi: {core}.",
        ),
    ),
    "missed": PositionRole(
        RoleField.TENSION,
        (
            "Điều dễ trượt qua: có thể bạn đang {tension}.",
            "Chỗ dễ bỏ sót: bạn có thể đang {tension}.",
            "Điều ít được để ý: có lúc bạn {tension}.",
        ),
        (
            "Chỗ bạn hay lướt qua: có khi đang {tension}.",
            "Chỗ sót kinh điển: bạn có thể {tension}.",
            "Góc khuất nhỏ: có lúc bạn {tension}.",
        ),
    ),
    "next": PositionRole(
        RoleField.RESOURCE,
        (
            "Điều cần tính tới: {core}.",
            "Bước tiếp dựa vào: {core}.",
            "Hành trang cho bước tiếp: {core}.",
        ),
        (
            "Mang theo khi bước: {core}.",
            "Nhớ kỹ trước khi lao: {core}.",
            "Hành lý cho bước tiếp: {core}.",
        ),
        step=True,
    ),
    # Five cards: clarity.
    "facts": PositionRole(
        RoleField.CORE,
        (
            "Điều có thể dựa vào: {core}.",
            "Dữ kiện đáng tin: {core}.",
            "Chỗ đứng vững lúc này: {core}.",
        ),
        (
            "Bằng chứng thật: {core}.",
            "Dữ kiện, không phải phim: {core}.",
            "Cái chắc tay nhất: {core}.",
        ),
    ),
    "assumption": PositionRole(
        RoleField.TENSION,
        (
            "Có thể bạn đang {tension}. Phần này chưa phải dữ kiện.",
            "Một giả định dễ có: bạn đang {tension}.",
            "Đây mới là phỏng đoán: có lúc bạn {tension}.",
        ),
        (
            "Kịch bản tự viết: bạn đang {tension}. Phần này chưa phải dữ kiện.",
            "Não tự điền chỗ trống: bạn đang {tension}.",
            "Phần đoán mò: có lúc bạn {tension}.",
        ),
    ),
    "need": PositionRole(
        RoleField.CORE,
        ("Điều bạn cần giữ: {core}.", "Nhu cầu thật ở đây: {core}.", "Điều đáng được giữ: {core}."),
        (
            "Thứ bạn thật cần: {core}.",
            "Điều bạn cần, nói thật: {core}.",
            "Nhu cầu chính chủ: {core}.",
        ),
    ),
    "agency": PositionRole(
        RoleField.RESOURCE,
        (
            "Phần nằm trong tay bạn: {resource}.",
            "Việc bạn tự làm được: {resource}.",
            "Trong tầm tay bạn: {resource}.",
        ),
        (
            "Việc bạn tự xử được: {resource}.",
            "Khỏi chờ ai, bạn có thể {resource}.",
            "Nút bấm trong tay bạn: {resource}.",
        ),
    ),
    # Five cards: loop.
    "trigger": PositionRole(
        RoleField.CORE,
        ("Điểm khởi phát: {core}.", "Chuyện hay bắt đầu từ: {core}.", "Cái cớ thường gặp: {core}."),
        (
            "Ngòi nổ quen mặt: {core}.",
            "Cảnh mở màn thường là: {core}.",
            "Chuyện hay nổ ra từ: {core}.",
        ),
    ),
    "habit": PositionRole(
        RoleField.TENSION,
        (
            "Phản xạ quen dễ là {tension}.",
            "Cách phản ứng quen thuộc: {tension}.",
            "Theo thói quen, bạn dễ {tension}.",
        ),
        (
            "Phản xạ tủ của bạn: {tension}.",
            "Như cài sẵn, bạn dễ {tension}.",
            "Lặp lại như phim cũ: bạn dễ {tension}.",
        ),
    ),
    "payoff": PositionRole(
        RoleField.CORE,
        ("Phản xạ ấy đem lại: {core}.", "Cái lợi ngắn hạn: {core}.", "Lý do nó còn đó: {core}."),
        ("Lợi lộc trước mắt: {core}.", "Nó cứu bạn lúc đó: {core}.", "Lý do nó bám dai: {core}."),
    ),
    "cost": PositionRole(
        RoleField.TENSION,
        (
            "Nếu cứ như cũ, về sau bạn dễ {tension}.",
            "Cái giá về sau: bạn dễ {tension}.",
            "Giữ mãi cách này, bạn dễ {tension}.",
        ),
        (
            "Cứ thế mãi thì bạn dễ {tension}.",
            "Hóa đơn về sau: bạn dễ {tension}.",
            "Phần phí ẩn: dễ {tension}.",
        ),
    ),
    "alternative": PositionRole(
        RoleField.RESOURCE,
        (
            "Nền cho cách mới: {core}.",
            "Đổi cách cần tính tới: {core}.",
            "Cách mới dựa vào: {core}.",
        ),
        ("Đổi kịch bản cần: {core}.", "Bản mới dựa vào: {core}.", "Trước khi đổi vai: {core}."),
        step=True,
    ),
    # Five cards: choice.
    "option_a": PositionRole(
        RoleField.OPTION,
        (
            "Hướng này mang lại: {core}. Cái giá cần tính: dễ {tension}.",
            "Phần được: {core}. Phần mất: dễ {tension}.",
            "Hướng này cho bạn: {core}. Nhưng cũng dễ khiến bạn {tension}.",
        ),
        (
            "Hướng này cho bạn: {core}. Phí phải trả: dễ {tension}.",
            "Điểm cộng: {core}. Điểm trừ: dễ {tension}.",
            "Món hời ở đây: {core}. Kèm theo đó, bạn dễ {tension}.",
        ),
    ),
    "option_b": PositionRole(
        RoleField.OPTION,
        (
            "Hướng này mang lại: {core}. Cái giá cần tính: dễ {tension}.",
            "Phần được: {core}. Phần mất: dễ {tension}.",
            "Hướng này cho bạn: {core}. Nhưng cũng dễ khiến bạn {tension}.",
        ),
        (
            "Hướng này cho bạn: {core}. Phí phải trả: dễ {tension}.",
            "Điểm cộng: {core}. Điểm trừ: dễ {tension}.",
            "Món hời ở đây: {core}. Kèm theo đó, bạn dễ {tension}.",
        ),
    ),
    "tradeoff": PositionRole(
        RoleField.TENSION,
        (
            "Điểm cần cân giữa hai hướng: dễ {tension}.",
            "Chỗ khó ở giữa: dễ {tension}.",
            "Cán cân dễ lệch khi bạn {tension}.",
        ),
        (
            "Bàn cân hai bên: dễ {tension}.",
            "Chỗ kẹt ở giữa: dễ {tension}.",
            "Điểm khó cân: dễ {tension}.",
        ),
    ),
    "criterion": PositionRole(
        RoleField.RESOURCE,
        (
            "Một tiêu chí để tự chốt: {resource}.",
            "Thước đo của riêng bạn: {resource}.",
            "Cách tự chốt: {resource}.",
        ),
        (
            "Thước đo tự chế: {resource}.",
            "Bài test nhỏ để chốt: {resource}.",
            "Tiêu chí của chính bạn: {resource}.",
        ),
        step=True,
    ),
    # Five cards: conversation.
    "feeling": PositionRole(
        RoleField.CORE,
        (
            "Cảm xúc gắn với: {core}.",
            "Điều đang chạm tới bạn: {core}.",
            "Phía sau cảm xúc: {core}.",
        ),
        ("Cảm xúc đang gõ cửa: {core}.", "Tim đang nói: {core}.", "Bên dưới cảm xúc: {core}."),
    ),
    "boundary": PositionRole(
        RoleField.RESOURCE,
        (
            "Ranh giới có thể nói rõ: {resource}.",
            "Một giới hạn đáng nói ra: {resource}.",
            "Giữ ranh giới bằng cách: {resource}.",
        ),
        (
            "Vạch ranh giới kiểu này: {resource}.",
            "Giới hạn đáng nói to: {resource}.",
            "Giữ phần mình bằng cách: {resource}.",
        ),
    ),
    "opening": PositionRole(
        RoleField.RESOURCE,
        ("Trước khi mở lời: {core}.", "Để mở lời dễ hơn: {core}.", "Nền cho câu mở đầu: {core}."),
        ("Trước khi gõ phím: {core}.", "Mở lời cho mượt: {core}.", "Chuẩn bị câu đầu: {core}."),
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
    core: str,
    tension: str,
    resource: str,
    frame: int = 0,
    roast: bool = False,
    lead: str | None = None,
) -> str:
    """The role's sentence: frame ``frame`` of the voice register, after an optional lead."""

    role = ROLES[position_key]
    template = (role.roast if roast else role.frames)[frame % FRAME_VARIANTS]
    text = template.format(core=core, tension=tension, resource=resource)
    if lead is None:
        return text
    return f"{lead} {text[:1].lower()}{text[1:]}"


def action_for(resource: str) -> str:
    """A step role's small action from the card's resource, without a "Thử nhé:" prefix."""

    step = resource.partition(", rồi ")[0]
    return f"{step[:1].upper()}{step[1:]}."
