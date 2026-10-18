"""Role-based meaning for each Tarot position (US-20 AC07/AC12, B2-2).

Each spread position has one role. The role picks which authored card field is read there
(core, tension or resource) and the sentence frame around it, and whether the position carries
the reading's small action. Only step roles carry an action. Frames hold no "Ý chính của lá",
"Thử nhé:" or "Ví dụ:" prefixes. Used for sessions that have a stored QuestionFrame (B2-1 and
later); earlier sessions keep the legacy renderer.

New copy in this module needs owner approval before release, and the module joins the fallback
approval scope at that point (docs/plans/2026-10-17-b2-2-tarot-roles-task.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

ROLE_COPY_VERSION = "tarot-roles-v1"


class RoleField(StrEnum):
    CORE = "core"  # what the card shows as already there
    TENSION = "tension"  # the pitfall or what is easy to miss
    RESOURCE = "resource"  # what the reader can do
    OPTION = "option"  # an option's gain (core) and its cost (tension)


@dataclass(frozen=True)
class PositionRole:
    field: RoleField
    frame: str  # direct-voice sentence around the field; {core} {tension} {resource}
    step: bool = False  # only step roles carry the reading's small action


# Keyed by the position keys of engine._POSITIONS.
ROLES: dict[str, PositionRole] = {
    # One card: what to look at, then what is in reach; it is also the step.
    "focus": PositionRole(
        RoleField.CORE, "Lá này cho thấy {core}. Phần nằm trong tay bạn: {resource}.", step=True
    ),
    # Three cards.
    "clear": PositionRole(RoleField.CORE, "Lá này cho thấy {core}."),
    "missed": PositionRole(RoleField.TENSION, "Điều dễ trượt qua: có thể bạn đang {tension}."),
    "next": PositionRole(RoleField.RESOURCE, "Điều cần tính tới khi bước tiếp: {core}.", step=True),
    # Five cards: clarity.
    "facts": PositionRole(RoleField.CORE, "Điều có thể dựa vào lúc này: {core}."),
    "assumption": PositionRole(
        RoleField.TENSION, "Có thể bạn đang {tension}; phần này chưa phải dữ kiện."
    ),
    "need": PositionRole(RoleField.CORE, "Điều bạn thật sự cần giữ: {core}."),
    "agency": PositionRole(RoleField.RESOURCE, "Phần nằm trong tay bạn: {resource}."),
    # Five cards: loop.
    "trigger": PositionRole(RoleField.CORE, "Chuyện thường bắt đầu từ đây: {core}."),
    "habit": PositionRole(RoleField.TENSION, "Phản xạ quen dễ là {tension}."),
    "payoff": PositionRole(RoleField.CORE, "Phản xạ ấy đỡ cho bạn lúc đó vì {core}."),
    "cost": PositionRole(RoleField.TENSION, "Nếu cứ như cũ, về sau bạn dễ {tension}."),
    "alternative": PositionRole(
        RoleField.RESOURCE, "Điều cần tính tới khi đổi cách phản ứng: {core}.", step=True
    ),
    # Five cards: choice.
    "option_a": PositionRole(
        RoleField.OPTION, "Hướng này mang lại: {core}. Cái giá cần tính: dễ {tension}."
    ),
    "option_b": PositionRole(
        RoleField.OPTION, "Hướng này mang lại: {core}. Cái giá cần tính: dễ {tension}."
    ),
    "tradeoff": PositionRole(RoleField.TENSION, "Điểm cần cân giữa hai hướng: dễ {tension}."),
    "criterion": PositionRole(
        RoleField.RESOURCE, "Một tiêu chí để tự chốt: {resource}.", step=True
    ),
    # Five cards: conversation.
    "feeling": PositionRole(RoleField.CORE, "Cảm xúc ở đây gắn với điều này: {core}."),
    "boundary": PositionRole(RoleField.RESOURCE, "Ranh giới có thể nói rõ: {resource}."),
    "opening": PositionRole(
        RoleField.RESOURCE, "Điều cần tính tới trước khi mở lời: {core}.", step=True
    ),
}

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


def meaning_for(position_key: str, *, core: str, tension: str, resource: str) -> str:
    role = ROLES[position_key]
    return role.frame.format(core=core, tension=tension, resource=resource)


def action_for(resource: str) -> str:
    """A step role's small action from the card's resource, without a "Thử nhé:" prefix."""

    step = resource.partition(", rồi ")[0]
    return f"{step[:1].upper()}{step[1:]}."
