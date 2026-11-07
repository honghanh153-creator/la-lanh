"""The owner's "Hôm nay" tab (US-24 §8): fixed header, ten rows, and the import validation.

Pure functions only. Nothing read from the Sheet grants access: a row is matched to a request by
its random code and date, and the database still decides who may read the frozen result and when.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.domains.human_tarot import policy
from app.domains.tarot.engine import TarotReadingEngine
from app.domains.tarot.knowledge import all_cards
from app.domains.tarot.models import TarotContext, TarotSpreadMap
from app.domains.tarot.quality import unsafe_claim

TAB = "Hôm nay"
HEADER = (
    "Mã yêu cầu",
    "Ngày nhận",
    "Giờ trả bài",
    "Chủ đề",
    "Câu hỏi",
    "Số lá",
    "Vị trí các lá",
    "Lá 1",
    "Lá 2",
    "Lá 3",
    "Lá 4",
    "Lá 5",
    "Bài đọc",
    "Bước nhỏ",
    "Sẵn sàng",
    "Trạng thái app",
    "Cần sửa",
)
LAST_COLUMN = "Q"
GRID = f"'{TAB}'!A1:{LAST_COLUMN}{1 + policy.DAILY_LIMIT}"
CODE = 0
DAY = 1
CARDS = slice(7, 12)
READING = 12
STEP = 13
READY = 14

STATUS_WAITING = "Đang chờ bài"
STATUS_IMPORTED = "Đã nhận bài"
STATUS_FIX = "Cần sửa"

READING_LENGTH = (40, 1500)
STEP_LENGTH = (8, 240)
CONTEXT_LABELS = {
    TarotContext.GENERAL: "Một chuyện",
    TarotContext.RELATIONSHIPS: "Quan hệ",
    TarotContext.WORK: "Công việc",
    TarotContext.COMMUNICATION: "Giao tiếp",
    TarotContext.ENERGY: "Năng lượng",
    TarotContext.SELF_CARE: "Bản thân",
}
_CODE = re.compile(policy.REQUEST_CODE_PATTERN)
_LINK = re.compile(
    r"https?://|www\.|\b[a-z0-9-]+\.(?:com|vn|net|org|io|me|ly|co|app|link)\b", re.IGNORECASE
)
_TAG = re.compile(r"<\s*[a-zA-Z/!][^>]*>")
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u2028\u2029]")


def row_number(slot_no: int) -> int:
    return slot_no + 1


def row_range(slot_no: int, first: str = "A", last: str = LAST_COLUMN) -> str:
    row = row_number(slot_no)
    return f"'{TAB}'!{first}{row}:{last}{row}"


def sheet_date(day: date) -> str:
    return day.strftime("%d/%m/%Y")


def request_cells(
    code: str, day: date, context: TarotContext, question: str, spread_map: TarotSpreadMap
) -> list[str]:
    """Columns A-G, written once by the app (RAW)."""

    positions = TarotReadingEngine.positions_for(spread_map)
    return [
        code,
        sheet_date(day),
        policy.RELEASE_TIME.strftime("%H:%M"),
        CONTEXT_LABELS[context],
        question,
        str(len(positions)),
        " · ".join(f"{index}. {label}" for index, (_, label) in enumerate(positions, 1)),
    ]


def padded(rows: list[list[Any]]) -> list[list[Any]]:
    """Google omits trailing empty cells and rows; give every row all 17 columns."""

    full = [list(row) + [""] * (len(HEADER) - len(row)) for row in rows]
    full += [[""] * len(HEADER) for _ in range(1 + policy.DAILY_LIMIT - len(full))]
    return full


def header_ok(grid: list[list[Any]]) -> bool:
    return tuple(_text(value) for value in grid[0]) == HEADER


def is_app_code(value: Any) -> bool:
    return _CODE.fullmatch(_text(value)) is not None


def code_rows(grid: list[list[Any]]) -> dict[str, list[int]]:
    """Code -> data row numbers (2..11) where it appears; a duplicate maps to several rows."""

    found: dict[str, list[int]] = {}
    for index, row in enumerate(grid[1:], start=2):
        code = _text(row[CODE])
        if code:
            found.setdefault(code, []).append(index)
    return found


def row_blank(row: list[Any]) -> bool:
    return all(_text(value) == "" for value in row)


def clear_decision(grid: list[list[Any]], code: str, slot_no: int) -> str:
    """What clearing a request's copy means for this grid (Codex r56), by binding not by code alone.

    ``gone``: the code is nowhere and the assigned row is empty. ``clear``: the assigned row holds
    the request (its code, or owner content with the code deleted). ``moved``: the code sits in
    another row. ``unverified``: the assigned row now carries another app code.
    """

    own = row_number(slot_no)
    found = code_rows(grid).get(code, [])
    if found:
        return "clear" if found == [own] else "moved"
    row = grid[own - 1]
    if row_blank(row):
        return "gone"
    if is_app_code(row[CODE]):
        return "unverified"
    return "clear"


def is_ready(value: Any) -> bool:
    return value is True or _text(value).upper() == "TRUE"


@dataclass(frozen=True)
class Validation:
    errors: tuple[str, ...]
    cards: tuple[str, ...] = ()
    reading: str = ""
    step: str = ""


def validate_row(row: list[Any], *, day: date, spread_map: TarotSpreadMap) -> Validation:
    """Check an owner-ticked row (US-24 AC15). Errors are closed codes, never cell content."""

    errors: list[str] = []
    if _text(row[DAY]) != sheet_date(day):
        errors.append("NGAY_KHONG_KHOP")
    needed = len(TarotReadingEngine.positions_for(spread_map))
    raw_cards = [_text(value) for value in row[CARDS]]
    filled = [value for value in raw_cards if value]
    if len(filled) != needed or any(not value for value in raw_cards[:needed]):
        errors.append("SO_LA_SAI")
    cards: list[str] = []
    for index, value in enumerate(raw_cards[:needed], start=1):
        if not value:
            continue
        card = _CATALOG.get(_fold(value))
        if card is None:
            errors.append(f"LA_{index}_KHONG_CO")
        else:
            cards.append(card)
    if len(set(cards)) != len(cards):
        errors.append("LA_TRUNG")
    reading = _plain(row[READING])
    step = _plain(row[STEP])
    errors += _length("BAI_DOC", reading, READING_LENGTH)
    errors += _length("BUOC_NHO", step, STEP_LENGTH)
    if any(_unsafe_markup(row[index]) for index in (READING, STEP)):
        errors.append("CO_LINK_HOAC_CONG_THUC")
    if unsafe_claim(f"{reading} {step}"):
        errors.append("CAU_KHANG_DINH_KHONG_AN_TOAN")
    if errors:
        return Validation(errors=tuple(dict.fromkeys(errors)))
    return Validation(errors=(), cards=tuple(cards), reading=reading, step=step)


def _length(prefix: str, value: str, bounds: tuple[int, int]) -> list[str]:
    if len(value) < bounds[0]:
        return [f"{prefix}_QUA_NGAN"]
    if len(value) > bounds[1]:
        return [f"{prefix}_QUA_DAI"]
    return []


def _unsafe_markup(value: Any) -> bool:
    text = _text(value)
    # Read with formulas unevaluated: a formula comes back starting with "=".
    return (
        text.startswith("=")
        or _LINK.search(text) is not None
        or _TAG.search(text) is not None
        or _CONTROL.search(text) is not None
    )


def _plain(value: Any) -> str:
    text = unicodedata.normalize("NFC", _text(value)).replace("\r\n", "\n").replace("\t", " ")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _text(value: Any) -> str:
    if value is None or value is False:
        return ""
    return str(value).strip()


def _fold(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


_CATALOG: dict[str, str] = {}
for _card in all_cards():
    _CATALOG[_fold(_card.title_vi)] = _card.id
    _CATALOG[_fold(_card.id)] = _card.id


def catalog_titles() -> list[str]:
    """The dropdown values for the "Lá" tab, in catalog order."""

    return [card.title_vi for card in all_cards()]
