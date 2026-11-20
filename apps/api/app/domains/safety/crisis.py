"""Self-harm and suicide language in free text a user typed (crisis safety layer, 14.11.2026).

``detect_crisis`` is the one check every free-text endpoint runs before it validates, stores or
reads the text. A match means: no reading, nothing stored, and the owner-approved notice
(``crisis_notice``) instead. The detector is deterministic and runs in memory; it never logs,
keeps or returns the text it reads.

How it reads text:

- Vietnamese with and without diacritics. Rules match on a folded copy (no accents, ``đ`` -> ``d``)
  aligned character by character with the accented copy. Every Vietnamese rule lists the accented
  spellings of its key word, so a key typed with accents must have the accents of the crisis
  reading ("tự sát", not "tủ sắt"; "tự tử", not "từ từ"). ``_rule`` refuses a rule without them.
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

from app.domains.content.copy_approval import approved_copy, copy_text

# Inputs are short (280 characters at most once validated); the guard runs before validation,
# so it only reads a bounded prefix of whatever arrived.
MAX_SCAN_CHARS = 2048

CRISIS_COPY_ID = "crisis.self_harm.notice"
# Owner decision 14.11.2026 (owner chose the sentence Codex proposed): the only text shown on a
# match; no hotline numbers and no links. Registered in copy_registry.json (category crisis,
# approver owner). A test keeps this identical to the registry entry; change both or neither.
CRISIS_NOTICE_TEXT = (
    "Mình rất tiếc vì bạn đang phải chịu điều này. Tarot không thể hỗ trợ tình huống này. "
    "Nếu bạn có thể làm hại bản thân lúc này, hãy tìm một người bạn tin cậy ở cạnh và nhờ hỗ "
    "trợ khẩn cấp."
)


@dataclass(frozen=True)
class CrisisNotice:
    copy_id: str
    text: str


def crisis_notice(surface_copy_id: str | None = None) -> CrisisNotice:
    """The notice for a surface (``surface_copy_id``), once the owner approved its sentence.

    Until then, and for Tarot, the approved Tarot notice is served: a surface never shows an
    unapproved crisis sentence and never shows nothing.
    """

    if surface_copy_id is not None:
        text = approved_copy(surface_copy_id)
        if text is not None:
            return CrisisNotice(copy_id=surface_copy_id, text=text)
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
    r"ha|nhe|ne|di|kieu nay|nhu the nay|o doi|o tren doi|o the gian|vl|vcl|vai|ghe|r|ri|lun)\b))"
)
# A benign word right after an unaccented "tu tu" reads as "từ từ" (slowly): "muốn từ từ tìm hiểu".
_SLOWLY_TAIL = (
    r"(?!\s+(?:tim|hoc|lam|xem|doc|tap|tien|hieu|biet|noi|suy|nghi|tinh|thich|mo|buoc|chuan|"
    r"quen|thu|lam quen|on|sap|xep|ke|chia|giai|sua|thay|doi|cho minh|cho em)\b)"
)


@dataclass(frozen=True)
class _Rule:
    """A folded pattern with a ``key`` group.

    ``forms``: when the key was typed with accents, it must be one of these spellings. Every
    Vietnamese rule lists them: folded text cannot tell "tự sát" from "tủ sắt", so a key typed
    with other accents is another phrase. English rules list none (accented text never counts).
    ``bare``: whether a key typed without any accents counts.
    ``plain_span``: a bare key counts only when the whole match is typed without accents, for keys
    that are everyday words without accents ("ngu mãi mãi" is "stupid forever", not "ngủ").
    ``plain``: other named groups that must be typed without accents ("mông chết" is not "mong").
    """

    pattern: re.Pattern[str]
    forms: frozenset[str]
    bare: bool = True
    plain_span: bool = False
    plain: tuple[str, ...] = ()

    def hit(self, accented: str, folded: str) -> bool:
        for match in self.pattern.finditer(folded):
            if any(
                accented[slice(*match.span(group))] != match.group(group) for group in self.plain
            ):
                continue
            start, end = match.span("key")
            typed = accented[start:end]
            if typed == folded[start:end]:
                if self.bare and (
                    not self.plain_span or accented[match.start() : match.end()] == match.group(0)
                ):
                    return True
            elif typed in self.forms:
                return True
        return False


def _forms(*parts: str | tuple[str, ...]) -> tuple[str, ...]:
    """Every spelling made of one choice per part: ``_forms("tự", ("làm", "gây"))``."""

    spellings = [""]
    for part in parts:
        choices = (part,) if isinstance(part, str) else part
        spellings = [f"{head} {choice}".strip() for head in spellings for choice in choices]
    return tuple(spellings)


def _rule(
    pattern: str,
    forms: tuple[str, ...],
    *,
    bare: bool = True,
    plain_span: bool = False,
    plain: tuple[str, ...] = (),
) -> _Rule:
    # A Vietnamese rule without accented spellings would match any accents (P1, 16.11).
    if not forms:
        raise ValueError(f"rule {pattern!r} lists no accented spellings; use _english()")
    return _Rule(re.compile(pattern), frozenset(forms), bare, plain_span, plain)


def _english(pattern: str) -> _Rule:
    return _Rule(re.compile(pattern), frozenset())


_ENDING = ("kết thúc", "kết liễu", "chấm dứt")

_RULES: tuple[_Rule, ...] = (
    # Words that name suicide or self-harm.
    _rule(r"\b(?P<key>tu sat)\b", ("tự sát",)),
    _rule(r"\b(?P<key>tu tu)\b", ("tự tử", "tự tữ"), bare=False),
    _rule(
        rf"\b{_INTENT} (?:{_SELF} )?(?:chuyen |viec )?(?P<key>tu tu)\b{_SLOWLY_TAIL}",
        ("tự tử", "tự tữ"),
    ),
    _rule(r"\b(?P<key>tu tu) (?:cho xong|cho roi|chet|luon)\b", ("tự tử", "tự tữ")),
    _rule(r"\b(?P<key>tu (?:van|vang))\b", ("tự vẫn", "tự vận"), bare=False),
    _rule(r"\b(?P<key>tu hai)\b", ("tự hại",), bare=False),
    _rule(r"\b(?P<key>tu hai) (?:ban than|chinh minh)\b", ("tự hại",)),
    _rule(
        r"\b(?P<key>tu (?:lam|gay) (?:dau|hai|thuong|ton thuong))\b",
        _forms("tự", ("làm", "gây"), ("đau", "hại", "thương", "tổn thương")),
    ),
    _rule(
        r"\b(?P<key>(?:lam|gay) (?:dau|hai|ton thuong)) (?:ban than|chinh minh)\b",
        _forms(("làm", "gây"), ("đau", "hại", "tổn thương")),
    ),
    _rule(
        r"(?<!\bbi )\b(?P<key>(?:rach|cat|cua) (?:co )?tay)\b(?! (?:ao|ninh|nguyen|bac|do)\b)",
        ("rạch tay", "cắt tay", "cứa tay", "rạch cổ tay", "cắt cổ tay", "cứa cổ tay"),
    ),
    _rule(r"\b(?P<key>chan song)\b", ("chán sống",)),
    # Methods.
    _rule(r"\b(?P<key>nhay lau)\b", ("nhảy lầu",), bare=False),
    _rule(rf"\b{_INTENT} (?P<key>nhay (?:lau|cau|song))\b", ("nhảy lầu", "nhảy cầu", "nhảy sông")),
    _rule(r"\b(?P<key>(?:treo|that) co)\b", ("treo cổ", "thắt cổ"), bare=False),
    _rule(rf"\b{_INTENT} (?P<key>(?:treo|that) co)\b", ("treo cổ", "thắt cổ")),
    _rule(
        r"\b(?P<key>uong (?:thuoc doc|thuoc chuot|thuoc tru sau|qua lieu|(?:ca|het) "
        r"(?:lo|vi|hop|nam) thuoc))\b",
        _forms("uống", ("thuốc độc", "thuốc chuột", "thuốc trừ sâu", "quá liều"))
        + _forms("uống", ("cả", "hết"), ("lọ", "vỉ", "hộp", "nắm"), "thuốc"),
    ),
    _rule(
        r"\b(?P<key>qua lieu thuoc|thuoc ngu cho (?:xong|chet|roi))\b",
        ("quá liều thuốc", *_forms("thuốc ngủ cho", ("xong", "chết", "rồi"))),
    ),
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
    _rule(r"\b(?P<key>tha chet)\b", ("thà chết",)),
    _rule(rf"\b{_SELF} (?:nen|phai) (?P<key>chet) (?:di|luon|cho)\b", ("chết",)),
    _rule(rf"\buoc (?:gi |chi )?(?:{_SELF} )?(?:duoc )?(?P<key>chet|die)\b", ("chết",)),
    _rule(
        rf"\b(?P<lead>mong) (?:{_SELF} )?(?:duoc )?(?P<key>chet|die)\b", ("chết",), plain=("lead",)
    ),
    _rule(r"\b(?:tim|nghi) (?:den |toi |ve )?(?P<key>cai chet)\b", ("cái chết",)),
    _rule(
        r"\b(?P<key>(?:ket thuc|ket lieu|cham dut) (?:cuoc doi|mang song|sinh mang|doi))"
        rf" (?:{_SELF}|nay|ban than|chinh minh)\b",
        _forms(_ENDING, ("cuộc đời", "mạng sống", "sinh mạng", "đời")),
    ),
    _rule(
        r"\b(?P<key>(?:ket thuc|ket lieu|cham dut) (?:cuoc doi|mang song|sinh mang))"
        r"(?=\s*(?:$|\.|cho xong|di\b|luon\b))",
        _forms(_ENDING, ("cuộc đời", "mạng sống", "sinh mạng")),
    ),
    _rule(r"\b(?P<key>ket lieu) (?:ban than|chinh minh|minh|doi minh)\b", ("kết liễu",)),
    # Said around the edges (week 1 target, 15.11): ending everything, not waking up, being a
    # burden, "everyone is better off without me", slang for leaving life, farewell signs.
    _rule(
        rf"\b(?:{_INTENT} |cho )?(?P<key>(?:ket thuc|cham dut) (?:moi thu|tat ca|het))"
        r"(?! voi)(?=\s*(?:$|\.|cho xong|cho roi|luon|di\b))",
        _forms(("kết thúc", "chấm dứt"), ("mọi thứ", "tất cả", "hết")),
    ),
    _rule(
        r"\b(?:muon|mun) (?:moi thu|tat ca|cuoc doi|cuoc song) (?P<key>(?:dung lai|ket thuc|"
        r"cham dut)) (?:han|mai mai|vinh vien|luon)\b",
        ("dừng lại", "kết thúc", "chấm dứt"),
    ),
    _rule(
        r"\bkhong (?:phai|can|con phai) (?P<key>song)"
        r"(?: (?:tiep |them )?nua\b| tiep(?=\s*(?:$|\.)))",
        ("sống",),
    ),
    _rule(
        r"\b(?P<key>song) (?:them|tiep|nua)(?: \.)? (?:cung |de |thi )?(?:chang|cha|khong|chi)"
        r"(?: \S+){0,2} (?:gi|kho|ganh|phien|met|ich|y nghia)\b",
        ("sống",),
    ),
    _rule(r"\b(?:khong|chang|ko) nen (?P<key>ton tai)\b", ("tồn tại",)),
    _rule(
        rf"\b(?:khong bao gio|vinh vien khong|mai mai khong|{_NOT}) (?:muon |mun )?"
        r"(?:thuc |tinh )?(?P<key>day) nua\b",
        ("dậy",),
    ),
    _rule(
        r"\b(?P<key>ngu) (?:mai mai|vinh vien|luon khong (?:thuc|tinh|day))\b",
        ("ngủ",),
        plain_span=True,
    ),
    _rule(
        rf"\b{_SELF} (?:se )?khong (?P<key>(?:tru|song|cam cu)) (?:duoc|noi) (?:toi|den|qua) "
        r"(?:cuoi tuan|mai|ngay mai|sang mai|toi mai|het (?:tuan|thang|nam))\b",
        ("trụ", "sống", "cầm cự"),
    ),
    _rule(
        rf"\b{_SELF} (?:la|chi la|nhu|thay {_SELF} la) (?:mot )?(?P<key>ganh nang) (?:cho|cua) ",
        ("gánh nặng",),
    ),
    _rule(
        rf"\b(?:(?:neu|khi) {_SELF} (?:bien mat|chet|khong con|di mai)|khong co {_SELF})"
        r"(?: \S+){0,7} "
        r"(?:do (?:kho|met|ganh|lo|phien|nang)|nhe nhom|nhe nguoi|vui|tot|hanh phuc|thanh than)"
        r"(?: \S+)? (?P<key>hon)\b",
        ("hơn",),
    ),
    _rule(
        r"\b(?:(?:out|ra|thoat|bien|di|roi) khoi|nghi choi(?: voi)?) (?P<key>(?:cuoc doi|the "
        r"gian|doi nay|trai dat))(?: nay)?(?! (?:cua|anh|chi|em|ho|nguoi|ban|ong|ba|no|ay)\b)",
        ("cuộc đời", "thế gian", "đời này", "trái đất"),
    ),
    _rule(
        r"\b(?P<key>di ban muoi)\b(?! (?:o|tai|cho (?:khach|nguoi)|kiem|online|lai)\b)",
        ("đi bán muối",),
    ),
    _english(r"\b(?P<key>unalive)\b"),
    _rule(
        r"\b(?P<key>thu (?:tuyet menh|vinh biet|tu biet))\b",
        _forms("thư", ("tuyệt mệnh", "vĩnh biệt", "từ biệt")),
    ),
    _rule(r"\bviet san (?P<key>thu) cho (?:tung|moi|tat ca|ca)\b", ("thư",)),
    _rule(r"\bchao (?P<key>vinh biet)\b", ("vĩnh biệt",)),
    _rule(
        r"\bchao (?P<key>tam biet|tu biet) (?:moi nguoi|tat ca|ca nha|gia dinh)(?: \S+){0,3} "
        r"(?:theo cach (?:cua )?(?:minh|rieng)|lan cuoi|mai mai)\b",
        ("tạm biệt", "từ biệt"),
    ),
    _rule(
        r"\b(?P<key>di xa)(?: \.)? (?:mai mai|vinh vien|(?:va )?(?:khong|chang) (?:bao gio )?"
        r"(?:quay lai|tro lai|tro ve|ve nua))(?=\s*(?:$|\.|(?:nua|dau|luon|bai|nhe|day)\b))"
        # Moving away for good is not a farewell: "đi xa, không quay lại, chuyển hẳn vào Nam".
        r"(?!.*\b(?:chuyen (?:han|nha|vao|ra|den|toi)|du hoc|lap nghiep|vao nam|ra bac|ve que)\b)",
        ("đi xa",),
    ),
    # A "last time" next to a farewell sign: giving things away, letters, nothing after today.
    _rule(
        r"^(?=.*\blan cuoi\b).*\b(?P<key>(?:cho|tang) het do(?: dac)?\b|"
        r"sau hom nay (?:khong|chang|se khong) (?:can|con))",
        _forms(("cho", "tặng"), "hết", ("đồ", "đồ đạc"))
        + _forms("sau hôm nay", ("không", "chẳng", "sẽ không"), ("cần", "còn")),
    ),
    # English basics.
    _english(r"\b(?P<key>kill(?:ing)? my ?self)\b"),
    _english(r"\b(?P<key>kms|kys myself)\b"),
    _english(r"\b(?P<key>suicid(?:e|al))\b(?! squad)"),
    _english(r"\b(?P<key>self ?harm(?:ing)?)\b"),
    _english(
        r"\b(?:want|wanna|wanting|going|gonna|plan|planning|try|trying|thinking about|"
        r"thought about) (?:to )?(?P<key>die|end my life|hurt(?:ing)? my ?self|"
        r"cut(?:ting)? my ?self)\b"
    ),
    _english(r"\b(?P<key>end(?:ing)? my (?:own )?life|take my (?:own )?life)\b"),
    _english(
        r"\b(?:dont|don t|do not) want to (?P<key>live|be alive|exist)"
        r"(?=\s*(?:$|\.|anymore\b|any more\b|like this\b))"
    ),
    _english(r"\b(?P<key>no reason to live|better off dead|wish i (?:was|were) dead)\b"),
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
    "mỏi lưng",
    "mỏi tay",
    "mỏi vai",
    "mỏi chân",
    "mỏi mắt",
    "nhức",
    "ê ẩm",
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
