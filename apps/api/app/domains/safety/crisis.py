"""Self-harm and suicide language in free text a user typed (crisis safety layer, 14.11.2026).

``detect_crisis`` is the one check every free-text endpoint runs before it validates, stores or
reads the text. A match means: no reading, nothing stored, and the owner-approved notice
(``crisis_notice``) instead. The detector is deterministic and runs in memory; it never logs,
keeps or returns the text it reads.

How it reads text:

- Vietnamese with and without diacritics. Rules match on a folded copy (no accents, ``đ`` -> ``d``)
  aligned character by character with the accented copy, so a rule can insist that its key word,
  when typed with accents, has the accents of the crisis reading ("tự tử", not "từ từ").
- Common teen spellings ("mún chít", "ko muốn sống", "muốn die") and stretched letters.
- Basic English ("kill myself", "want to die", "suicidal", "kms").
- Figurative "chết" is left alone: "chết cười", "deadline dí chết", "mệt chết đi được",
  "đẹp chết người", and "muốn chết" right after a body or mood word ("đói muốn chết").

It errs towards the notice: a false positive costs one short notice instead of a reading; a miss
puts self-harm text into a reading. The phrase table in ``tests/safety/crisis_phrases.py`` is the
spec.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.domains.content.copy_approval import copy_text

# Inputs are short (280 characters at most once validated); the guard runs before validation,
# so it only reads a bounded prefix of whatever arrived.
MAX_SCAN_CHARS = 2048

CRISIS_COPY_ID = "crisis.self_harm.notice"
# Owner decision 14.11.2026, owner's own wording ("app không hỗ trợ"): the only text shown on a
# match; no hotline numbers and no links. Registered in copy_registry.json (category crisis,
# approver owner). A test keeps this identical to the registry entry; change both or neither.
CRISIS_NOTICE_TEXT = "Ứng dụng không hỗ trợ nội dung này."


@dataclass(frozen=True)
class CrisisNotice:
    copy_id: str
    text: str


def crisis_notice() -> CrisisNotice:
    return CrisisNotice(copy_id=CRISIS_COPY_ID, text=copy_text(CRISIS_COPY_ID, CRISIS_NOTICE_TEXT))


# --- normalisation -------------------------------------------------------------------------

_SENTENCE_MARK = re.compile(r"[.,!?;:…\n\r]+")
_NOT_WORD = re.compile(r"[^\w.]|_")
_STRETCHED = re.compile(r"(\w)\1{2,}")


def _fold_char(char: str) -> str:
    if char == "đ":
        return "d"
    base = "".join(c for c in unicodedata.normalize("NFD", char) if unicodedata.category(c) != "Mn")
    # Exactly one character out keeps the folded copy aligned with the accented one.
    return base if len(base) == 1 else char


def fold(text: str) -> str:
    """Lower case, no Vietnamese diacritics, ``đ`` -> ``d``; one character per character."""

    return "".join(_fold_char(char) for char in text)


def normalize(text: str) -> tuple[str, str]:
    """(accented, folded) copies of the same tokens, aligned character by character.

    Sentence marks become a ``.`` token so a rule can see where a clause ends; any other symbol
    becomes a space; a letter stretched three times or more ("chếttt") counts once.
    """

    lowered = unicodedata.normalize("NFC", text[:MAX_SCAN_CHARS]).casefold()
    lowered = "".join(c for c in lowered if unicodedata.category(c) != "Mn")
    lowered = _SENTENCE_MARK.sub(" . ", lowered)
    lowered = _NOT_WORD.sub(" ", lowered)
    lowered = _STRETCHED.sub(r"\1", lowered)
    accented = " ".join(lowered.split())
    return accented, fold(accented)


# --- vocabulary (folded) -------------------------------------------------------------------

_NOT = r"(?:khong|ko|k|kh|hok|hong|khum|hem|hk|kg|cha|chang|het)"
_WANT_LIVE = r"(?:muon|mun|thiet|con muon|muon con|thich)"
_INTENT = r"(?:muon|mun|dinh|tinh|se|sap|nghi den|nghi toi|nghi ve|co y dinh|thu|chi muon)"
_SELF = r"(?:toi|minh|em|tao|to|tui|anh|chi|con|chau)"
# "sống" only counts as "to live on" when the clause ends or carries on in these ways; "không
# muốn sống ở Hà Nội" or "sống chung với bố mẹ" is about where and with whom.
_LIVE_TAIL = (
    r"(?=\s*(?:$|\.|(?:nua|tiep|them|tren|lam|roi|chut|day|qua|luon|that|ma|nhung|va|thi|a|ah|"
    r"ha|nhe|ne|di|kieu nay|nhu the nay|o doi|o tren doi|o the gian|vl|vcl|vai|ghe)\b))"
)
# A benign word right after an unaccented "tu tu" reads as "từ từ" (slowly): "muốn từ từ tìm hiểu".
_SLOWLY_TAIL = (
    r"(?!\s+(?:tim|hoc|lam|xem|doc|tap|tien|hieu|biet|noi|suy|nghi|tinh|thich|mo|buoc|chuan|"
    r"quen|thu|lam quen|on|sap|xep|ke|chia|giai|sua|thay|doi|cho minh|cho em)\b)"
)


@dataclass(frozen=True)
class _Rule:
    """A folded pattern with a ``key`` group.

    ``forms``: when the key was typed with accents, it must be one of these spellings (None: any).
    ``bare``: whether a key typed without any accents counts.
    """

    pattern: re.Pattern[str]
    forms: frozenset[str] | None = None
    bare: bool = True

    def hit(self, accented: str, folded: str) -> bool:
        for match in self.pattern.finditer(folded):
            start, end = match.span("key")
            typed = accented[start:end]
            if typed == folded[start:end]:
                if self.bare:
                    return True
            elif self.forms is None or typed in self.forms:
                return True
        return False


def _rule(pattern: str, forms: tuple[str, ...] | None = None, *, bare: bool = True) -> _Rule:
    return _Rule(re.compile(pattern), frozenset(forms) if forms is not None else None, bare)


_RULES: tuple[_Rule, ...] = (
    # Words that name suicide or self-harm.
    _rule(r"\b(?P<key>tu sat)\b"),
    _rule(r"\b(?P<key>tu tu)\b", ("tự tử", "tự tữ"), bare=False),
    _rule(rf"\b{_INTENT} (?:{_SELF} )?(?P<key>tu tu)\b{_SLOWLY_TAIL}", ("tự tử", "tự tữ")),
    _rule(r"\b(?P<key>tu tu) (?:cho xong|cho roi|chet|luon)\b", ("tự tử", "tự tữ")),
    _rule(r"\b(?P<key>tu (?:van|vang))\b", ("tự vẫn", "tự vận"), bare=False),
    _rule(r"\b(?P<key>tu hai)\b", ("tự hại",), bare=False),
    _rule(r"\b(?P<key>tu hai) (?:ban than|chinh minh)\b"),
    _rule(r"\b(?P<key>tu (?:lam|gay) (?:dau|hai|thuong|ton thuong))\b"),
    _rule(r"\b(?P<key>(?:lam|gay) (?:dau|hai|ton thuong)) (?:ban than|chinh minh)\b"),
    _rule(r"(?<!\bbi )\b(?P<key>(?:rach|cat|cua) (?:co )?tay)\b(?! ao)"),
    _rule(r"\b(?P<key>chan song)\b", ("chán sống",)),
    # Methods.
    _rule(r"\b(?P<key>nhay lau)\b", ("nhảy lầu",), bare=False),
    _rule(rf"\b{_INTENT} (?P<key>nhay (?:lau|cau|song))\b", ("nhảy lầu", "nhảy cầu", "nhảy sông")),
    _rule(r"\b(?P<key>(?:treo|that) co)\b", ("treo cổ", "thắt cổ"), bare=False),
    _rule(rf"\b{_INTENT} (?P<key>(?:treo|that) co)\b", ("treo cổ", "thắt cổ")),
    _rule(
        r"\b(?P<key>uong (?:thuoc doc|thuoc chuot|thuoc tru sau|qua lieu|(?:ca|het) "
        r"(?:lo|vi|hop|nam) thuoc))\b"
    ),
    _rule(r"\b(?P<key>qua lieu thuoc|thuoc ngu cho (?:xong|chet|roi))\b"),
    # Not wanting to live or to exist.
    _rule(rf"\b{_NOT} {_WANT_LIVE} (?P<key>song){_LIVE_TAIL}", ("sống",)),
    _rule(r"\b(?P<key>song) (?:de )?(?:lam )?gi nua\b", ("sống",)),
    _rule(r"\bkhong (?:con )?(?:ly do|li do|le song) (?:de )?(?P<key>song)\b", ("sống",)),
    _rule(r"\bkhong (?:dang|xung dang) (?:duoc )?(?P<key>song)\b", ("sống",)),
    _rule(rf"\b{_NOT} (?:muon|mun) (?P<key>ton tai)\b", ("tồn tại",)),
    _rule(
        rf"\buoc (?:gi|chi) (?:{_SELF} )?(?:khong|chua tung|chua bao gio) (?P<key>ton tai)\b",
        ("tồn tại",),
    ),
    _rule(
        r"\b(?:muon|mun) (?P<key>bien mat) (?:mai mai|vinh vien|khoi (?:the gian|the gioi|"
        r"cuoc doi|trai dat|doi nay|cuoc song))\b",
        ("biến mất",),
    ),
    # Wishing for death.
    _rule(
        r"\b(?P<key>chet|chit)(?: di| luon| quach| me| phat)? cho (?:xong|roi|nhe|khoe|yen)\b",
        ("chết", "chít"),
    ),
    _rule(r"\b(?P<key>chet) quach\b", ("chết",)),
    _rule(r"\btha (?P<key>chet)\b", ("chết",)),
    _rule(rf"\buoc (?:gi |chi )?(?:{_SELF} )?(?:duoc )?(?P<key>chet|die)\b", ("chết",)),
    _rule(rf"\bmong (?:{_SELF} )?(?:duoc )?(?P<key>chet|die)\b", ("chết",)),
    _rule(r"\b(?:tim|nghi) (?:den |toi |ve )?(?P<key>cai chet)\b", ("cái chết",)),
    _rule(
        r"\b(?P<key>(?:ket thuc|ket lieu|cham dut) (?:cuoc doi|mang song|sinh mang|doi))"
        rf" (?:{_SELF}|nay|ban than|chinh minh)\b"
    ),
    _rule(
        r"\b(?P<key>(?:ket thuc|ket lieu|cham dut) (?:cuoc doi|mang song|sinh mang))"
        r"(?=\s*(?:$|\.|cho xong|di\b|luon\b))"
    ),
    _rule(r"\b(?P<key>ket lieu) (?:ban than|chinh minh|minh|doi minh)\b", ("kết liễu",)),
    # English basics.
    _rule(r"\b(?P<key>kill(?:ing)? my ?self)\b"),
    _rule(r"\b(?P<key>kms|kys myself)\b"),
    _rule(r"\b(?P<key>suicid(?:e|al))\b(?! squad)"),
    _rule(r"\b(?P<key>self ?harm(?:ing)?)\b"),
    _rule(r"\b(?P<key>unalive (?:my ?self|me))\b"),
    _rule(
        r"\b(?:want|wanna|wanting|going|gonna|plan|planning|try|trying|thinking about|"
        r"thought about) (?:to )?(?P<key>die|end my life|hurt(?:ing)? my ?self|"
        r"cut(?:ting)? my ?self)\b"
    ),
    _rule(r"\b(?P<key>end(?:ing)? my (?:own )?life|take my (?:own )?life)\b"),
    _rule(
        r"\b(?:dont|don t|do not) want to (?P<key>live|be alive|exist)"
        r"(?=\s*(?:$|\.|anymore\b|any more\b|like this\b))"
    ),
    _rule(r"\b(?P<key>no reason to live|better off dead|wish i (?:was|were) dead)\b"),
)


# --- "muốn chết": real wish or figure of speech ------------------------------------------

_WANT_DIE = re.compile(r"\b(?P<want>muon|mun|thich)(?: duoc| di)? (?P<key>chet|chit|die)\b")
_WANT_FORMS = frozenset({"muốn", "mún", "thích"})
_DIE_FORMS = frozenset({"chết", "chít"})
# Right before "muốn": a speaker or a modal makes it a statement about oneself.
_SELF_OR_MODAL = frozenset(
    {
        "toi",
        "minh",
        "em",
        "tao",
        "to",
        "tui",
        "anh",
        "chi",
        "con",
        "chau",
        "rat",
        "van",
        "lai",
        "cung",
        "hay",
        "cu",
        "dang",
        "luon",
        "that",
        "su",
    }
)
_SELF_OR_MODAL_PAIRS = frozenset(
    {"bat dau", "that su", "thuc su", "nhieu luc", "co luc", "doi khi", "nhieu khi"}
)
# Mood words: when they come shortly before "muốn chết", it is a cry for help, not a figure.
_DISTRESS = (
    "chán",
    "buồn",
    "tuyệt vọng",
    "bất lực",
    "cô đơn",
    "áp lực",
    "đau lòng",
    "kiệt sức",
    "bế tắc",
    "trầm cảm",
    "mệt mỏi",
    "khổ",
)
# Body states and small feelings used as "to death" intensifiers: "đói muốn chết".
_INTENSIFIERS = (
    "mệt",
    "đói",
    "khát",
    "nóng",
    "lạnh",
    "sợ",
    "lo",
    "ngại",
    "quê",
    "ngượng",
    "cười",
    "ghen",
    "thèm",
    "nhớ",
    "ngứa",
    "cay",
    "run",
    "bận",
    "ồn",
    "tức",
    "giận",
    "khó",
    "đau",
    "buồn ngủ",
    "buồn cười",
    "xấu hổ",
    "mắc cỡ",
    "hồi hộp",
    "đau bụng",
    "đau đầu",
    "đau răng",
    "nhức đầu",
    "đau lưng",
    "đau chân",
    "đau họng",
    "nóng ruột",
)


def _phrase_at(words: list[str], folded_words: list[str], index: int, phrase: str) -> bool:
    """``phrase`` (accented) starts at ``index``: typed with its accents, or with none at all."""

    parts = phrase.split()
    window = words[index : index + len(parts)]
    if len(window) != len(parts):
        return False
    typed = " ".join(window)
    if typed == phrase:
        return True
    plain = " ".join(folded_words[index : index + len(parts)])
    return typed == plain and plain == fold(phrase)


def _found(words: list[str], folded_words: list[str], phrases: tuple[str, ...]) -> set[int]:
    """Indexes of the words covered by any of ``phrases`` (longest phrases first)."""

    covered: set[int] = set()
    for phrase in sorted(phrases, key=lambda p: -len(p.split())):
        size = len(phrase.split())
        for index in range(len(words)):
            if covered.intersection(range(index, index + size)):
                continue
            if _phrase_at(words, folded_words, index, phrase):
                covered.update(range(index, index + size))
    return covered


def _wants_to_die(accented: str, folded: str) -> bool:
    for match in _WANT_DIE.finditer(folded):
        want_start, want_end = match.span("want")
        key_start, key_end = match.span("key")
        want, key = accented[want_start:want_end], accented[key_start:key_end]
        if want != folded[want_start:want_end] and want not in _WANT_FORMS:
            continue  # "muộn chết" (late), not "muốn chết"
        if key != folded[key_start:key_end] and key not in _DIE_FORMS:
            continue
        before = accented[:want_start].split()
        folded_before = folded[:want_start].split()
        if "." in before:
            cut = len(before) - before[::-1].index(".")
            before, folded_before = before[cut:], folded_before[cut:]
        before, folded_before = before[-3:], folded_before[-3:]
        if folded_before and (
            folded_before[-1] in _SELF_OR_MODAL
            or " ".join(folded_before[-2:]) in _SELF_OR_MODAL_PAIRS
        ):
            return True
        distress = _found(before, folded_before, _DISTRESS)
        figurative = _found(before, folded_before, _INTENSIFIERS)
        # A distress word wins over an intensifier only where it is not part of one
        # ("buồn ngủ" is sleepy, not sad).
        if distress - figurative:
            return True
        if figurative:
            continue
        return True
    return False


def detect_crisis(text: str) -> bool:
    """True when ``text`` reads as self-harm or suicide intent."""

    if not text or not text.strip():
        return False
    accented, folded = normalize(text)
    if _wants_to_die(accented, folded):
        return True
    return any(rule.hit(accented, folded) for rule in _RULES)
