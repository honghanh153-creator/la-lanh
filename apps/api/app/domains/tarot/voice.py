"""Reviewed roast frames for local Tarot readings (owner decision 2026-10-11).

Roast only frames the reading: card meanings, order, positions, scenes,
reflection questions and the action instruction stay identical to the default
voice. Energy/self-care readings get the gentle frame. Sensitive questions
(health, safety, crisis, grief, legal or money trouble) use the default voice.
"""

from __future__ import annotations

import re
import unicodedata

from app.domains.tarot.models import TarotContext, TarotQuestionIntent, TarotVoice

GENTLE_CONTEXTS = frozenset({TarotContext.ENERGY, TarotContext.SELF_CARE})

ROAST_HEADLINES: dict[TarotQuestionIntent, str] = {
    TarotQuestionIntent.CLARITY: (
        "Thôi nào thám tử, tách chuyện đã xảy ra khỏi chuyện mình tự đoán."
    ),
    TarotQuestionIntent.BOUNDARY: (
        "Làm vừa lòng cả thế giới là nhiệm vụ bất khả thi, nói rõ giới hạn trước."
    ),
    TarotQuestionIntent.NEXT_STEP: "Chưa cần viết hết cả phim, chọn một cảnh nhỏ để thử trước.",
    TarotQuestionIntent.COMMUNICATION: "Nói câu chính trước, phần giải thích dài như sớ để sau.",
    TarotQuestionIntent.SELF_CHECK: (
        "Não đang mở 12 tab, gọi đúng tên điều bạn đang cảm và đang cần."
    ),
}
GENTLE_HEADLINES: dict[TarotQuestionIntent, str] = {
    TarotQuestionIntent.CLARITY: "Từ từ thôi, tách điều đã xảy ra khỏi điều bạn đang đoán nha.",
    TarotQuestionIntent.BOUNDARY: "Bạn đâu cần làm vừa lòng tất cả, nói rõ giới hạn trước nha.",
    TarotQuestionIntent.NEXT_STEP: (
        "Nhẹ thôi, chọn một bước nhỏ để thử, chưa cần chốt cả câu chuyện."
    ),
    TarotQuestionIntent.COMMUNICATION: "Nói câu chính trước nha, phần giải thích để sau cũng được.",
    TarotQuestionIntent.SELF_CHECK: (
        "Chậm lại chút, gọi đúng điều bạn đang cảm và điều bạn đang cần."
    ),
}

SUMMARY_OPENERS: dict[TarotContext, str] = {
    TarotContext.GENERAL: "Tóm gọn cho người bận rộn, không vòng vo nha.",
    TarotContext.RELATIONSHIPS: "Không đoán lòng ai hết, mình chỉ soi phần bạn tự làm được.",
    TarotContext.WORK: "Tóm gọn cho người đang ôm việc tới cổ, không vòng vo nha.",
    TarotContext.COMMUNICATION: "Tóm gọn trước khi bạn kịp gõ thêm một đoạn dài nha.",
    TarotContext.ENERGY: "Tóm gọn nhẹ nhàng, đọc xong là nghỉ được liền.",
    TarotContext.SELF_CARE: "Tóm gọn nhẹ nhàng, không ai bắt bạn phải gồng đâu.",
}

# Position-group tails appended after the unchanged meaning sentence.
_MEANING_GROUPS: dict[str, str] = {
    "facts": "facts",
    "trigger": "facts",
    "assumption": "assumption",
    "habit": "assumption",
    "need": "need",
    "feeling": "need",
    "payoff": "need",
    "agency": "agency",
    "alternative": "agency",
    "boundary": "agency",
    "criterion": "agency",
    "opening": "agency",
    "tradeoff": "agency",
    "next": "agency",
    "cost": "cost",
    "option_a": "option",
    "option_b": "option",
    "missed": "missed",
}
ROAST_MEANING_TAILS: dict[str, str] = {
    "facts": "Chuyện đã xảy ra mới tính, phim tự dựng thì để sau.",
    "assumption": "Đoán thì dễ, kiểm chứng mới là trùm cuối.",
    "need": "Gọi tên được là đỡ được một nửa rồi đó.",
    "agency": "Phần này nằm trong tay bạn, khỏi chờ ai duyệt.",
    "cost": "Cứ lặp lại y chang thì hóa đơn về sau cũng y chang.",
    "option": "Hướng nào cũng có giá, xem kỹ bảng giá trước nha.",
    "missed": "Chỗ này hay bị lướt qua lắm nha.",
    "default": "Nghe thì đơn giản, làm thật mới thấy hay.",
}
GENTLE_MEANING_TAILS: dict[str, str] = {
    "facts": "Chỉ cần nhìn điều đã xảy ra, chưa cần gồng thêm.",
    "assumption": "Đoán nhiều dễ mệt, mình kiểm chứng từ từ nha.",
    "need": "Gọi tên được là đã nhẹ hơn rồi.",
    "agency": "Phần này bạn tự chọn được, nhẹ nhàng thôi.",
    "cost": "Nhận ra sớm để đỡ mệt về sau nha.",
    "option": "Hướng nào cũng có giá, xem nhẹ nhàng từng bên.",
    "missed": "Chỗ này dễ bị lướt qua khi đang mệt.",
    "default": "Nhìn vậy là đủ cho hôm nay rồi.",
}
ROAST_ACTION_FRAMES: tuple[str, ...] = (
    "Thôi nào, làm liền:",
    "Bài tập nhỏ, khỏi gồng:",
    "Chốt kèo nhỏ này nha:",
    "Một nước đi gọn gàng:",
    "Làm thử cho biết nè:",
)
GENTLE_ACTION_FRAMES: tuple[str, ...] = (
    "Nhẹ nhàng thôi:",
    "Một việc nhỏ cho mình:",
    "Từ từ làm nha:",
    "Vừa sức thôi:",
    "Chậm mà đều nha:",
)


def _fold(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(char) != "Mn"
    ).replace("đ", "d")


# Exact (diacritic) words are short and would collide once folded; folded
# phrases are long enough to match unaccented typing safely.
_SENSITIVE_EXACT = re.compile(
    r"\b(?:bệnh|ốm|đau|thuốc|mang thai|sảy thai|kiện|nợ|tiền|tang|chết|lo âu|mất ngủ|"
    r"an toàn|nguy hiểm|đe dọa|đe doạ|bị đánh|nghiện|công an)\b",
    re.IGNORECASE,
)
_SENSITIVE_FOLDED = re.compile(
    r"\b(?:tu sat|tu hai|tu lam dau|muon chet|khong muon song|tram cam|roi loan|"
    r"khung hoang|tuyet vong|hoang loan|suc khoe|benh vien|nam vien|phau thuat|chan doan|"
    r"qua doi|mat nguoi than|dam tang|dau buon|bao hanh|bao luc|xam hai|quay roi|"
    r"chia tay|ly hon|mat viec|pha san|vay tien|phap ly|toa an|luat su|dau tu|co phieu)\b"
)


def roast_allowed(question: str) -> bool:
    """False for questions where teasing could hurt; those use the default voice."""

    return not (_SENSITIVE_EXACT.search(question) or _SENSITIVE_FOLDED.search(_fold(question)))


def effective_voice(voice: TarotVoice, question: str) -> TarotVoice:
    if voice is TarotVoice.ROAST and not roast_allowed(question):
        return TarotVoice.PLAYFUL_GROUNDED
    return voice


def meaning_tail(position_key: str, context: TarotContext) -> str:
    tails = GENTLE_MEANING_TAILS if context in GENTLE_CONTEXTS else ROAST_MEANING_TAILS
    return tails[_MEANING_GROUPS.get(position_key, "default")]


def action_frame(index: int, context: TarotContext) -> str:
    frames = GENTLE_ACTION_FRAMES if context in GENTLE_CONTEXTS else ROAST_ACTION_FRAMES
    return frames[index % len(frames)]


def roast_headline(intent: TarotQuestionIntent, context: TarotContext) -> str:
    return (GENTLE_HEADLINES if context in GENTLE_CONTEXTS else ROAST_HEADLINES)[intent]
