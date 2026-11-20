"""Pending/approved flag for new user-facing copy (owner decision 06.11.2026).

New sentences enter ``copy_registry.json`` as ``pending``. Runtime serves an entry only when it
is ``approved`` with a matching digest; otherwise the caller's current approved sentence is
served. Codex may approve a daily batch (``scripts/codex-copy-review.mjs``); privacy, consent,
crisis and safety copy stays owner-only. ``scripts.fallback_approval`` pins approved entries
only, so adding a pending entry does not trip the owner gate.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

REGISTRY_PATH = Path(__file__).with_name("copy_registry.json")
REGISTRY_VERSION = "copy-registry/v1"
STATUSES = frozenset({"pending", "approved"})
APPROVERS = frozenset({"codex", "owner"})
OWNER_ONLY_CATEGORIES = frozenset({"privacy", "consent", "crisis", "safety"})


def copy_digest(text: str) -> str:
    return sha256(unicodedata.normalize("NFC", text).encode()).hexdigest()


# Copy lint (register #177, PV-15). Machine-written copy goes through an auto loop, so text
# shown to users must never carry a link, a contact detail or an unfilled template slot.
# Every rule applies to pending and approved entries alike; an approved entry that breaks
# one is not servable, so runtime falls back to the caller's current approved sentence.
#
# The two classes are closed by definition, not by a list of known spellings (review r7 of #411):
#
# Link. Decided by Python's IDNA codec, not by a character class (review r10 of #411): a word
# (no space inside) with a dot is a link when the codec encodes it as a host name of two or more
# labels and the last label has two or more characters and does not start with a digit. Any
# script, combining marks and symbols count ("vidu.vn", "vi-du.рф", "vi-du.भारत", "☕.test"),
# as do punycode labels ("xn--p1ai") and the other IDNA dots (U+3002, U+FF0E, U+FF61).
# Punctuation around the word is not part of it ("(vidu.com)."). A word is first cut at the URL
# separators "/", "?", "#", "\\" and ":" and every piece is checked on its own, so a path, query,
# fragment or port after the host ("vidu.test/trang?x=1.5", "vidu.test/a..b", "vidu.com:8080")
# never hides it (review r11 of #411). There is no list of suffixes,
# so sentences glued
# together ("xong.Sau", "nhỏ.Rồi") count as a link too: the copy adds the space. Numbers ("1.5",
# "2.10.3", "50.000đ", "3.5km") are not links; an IPv4 address, a scheme ("https://") and "www."
# are. text_lint_problems also reads a folded text, so case, full-width letters and invisible
# characters are not ways around the rule.
#
# Template slot. Read by printf_slots(), a tokenizer that walks the printf grammar the way
# Python's "%" operator does, not by a pattern (review r9 of #411):
#   "%" ["(" key ")" | n "$"] flags* [width] ["." [precision]] [length] conversion
# - key: any characters, newlines included, up to the ")" that closes it (nested parentheses
#   counted), as Python reads it;
# - flags "-+ #0'"; width and precision: digits or "*" (C also "*m$"); the precision may be
#   empty ("%.s", "%05.f");
# - length: Python's h/l/L and C's hh/ll/q/j/z/t/I/I32/I64/w;
# - conversion: every letter of Python and C printf (diouxXeEfFgGaAcrspn, C/S/m).
# "%%" is a literal percent sign. One exception, on purpose: a space flag with nothing else
# ("50% dung lượng") is plain text. Tests compare the tokenizer with Python's own "%".
_SLOT_FLAGS = frozenset("-+ #0'")
_SLOT_LENGTHS = ("hh", "ll", "I64", "I32", "h", "l", "L", "q", "j", "z", "t", "I", "w")
_SLOT_CONVERSIONS = frozenset("diouxXeEfFgGaAcsrpnCSm")
_ASCII_DIGITS = frozenset("0123456789")


def _slot_number(text: str, at: int) -> int:
    """End of a width or precision at ``at``: digits, or "*" with an optional "m$"."""

    if at < len(text) and text[at] == "*":
        end = at + 1
        digits = end
        while digits < len(text) and text[digits] in _ASCII_DIGITS:
            digits += 1
        return digits + 1 if digits > end and digits < len(text) and text[digits] == "$" else end
    while at < len(text) and text[at] in _ASCII_DIGITS:
        at += 1
    return at


def printf_slots(text: str) -> tuple[tuple[int, int], ...]:
    """(start, end) of every printf-style slot in ``text``; see the grammar above."""

    slots: list[tuple[int, int]] = []
    at = 0
    while (start := text.find("%", at)) != -1:
        at = start + 1
        if at < len(text) and text[at] == "%":
            at += 1
            continue
        cursor = at
        named = False
        if cursor < len(text) and text[cursor] == "(":
            depth, cursor = 1, cursor + 1
            while cursor < len(text) and depth:
                depth += {"(": 1, ")": -1}.get(text[cursor], 0)
                cursor += 1
            if depth:
                continue  # an unclosed key is not a slot
            named = True
        else:
            digits = cursor
            while digits < len(text) and text[digits] in _ASCII_DIGITS:
                digits += 1
            if digits > cursor and digits < len(text) and text[digits] == "$":
                cursor, named = digits + 1, True
        flags_start = cursor
        while cursor < len(text) and text[cursor] in _SLOT_FLAGS:
            cursor += 1
        flags = text[flags_start:cursor]
        rest_start = cursor
        cursor = _slot_number(text, cursor)
        if cursor < len(text) and text[cursor] == ".":
            cursor = _slot_number(text, cursor + 1)
        length = next((form for form in _SLOT_LENGTHS if text.startswith(form, cursor)), "")
        cursor += len(length)
        if cursor >= len(text) or text[cursor] not in _SLOT_CONVERSIONS:
            continue
        plain_space = not named and set(flags) == {" "} and cursor == rest_start
        if not plain_space:
            slots.append((start, cursor + 1))
            at = cursor + 1
    return tuple(slots)


_IDNA_DOTS = re.compile("[.\u3002\uff0e\uff61]")
# Review r11 of #411: a host is cut out of its word at these before its labels are checked.
_URL_SEPARATORS = re.compile(r"[/?#\\:]")


def _strip_punctuation(word: str) -> str:
    start, end = 0, len(word)
    while start < end and unicodedata.category(word[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(word[end - 1]).startswith("P"):
        end -= 1
    return word[start:end]


def idna_hosts(text: str) -> tuple[str, ...]:
    """Words of ``text`` that Python's IDNA codec reads as a host name; see the rule above."""

    hosts: list[str] = []
    for word in text.split():
        for piece in _URL_SEPARATORS.split(word):
            host = _strip_punctuation(piece)
            labels = _IDNA_DOTS.split(host)
            if len(labels) < 2 or not all(labels):
                continue
            last = labels[-1]
            if len(last) < 2 or last[0].isdecimal():
                continue
            try:
                host.encode("idna")
            except UnicodeError:
                continue
            hosts.append(host)
    return tuple(hosts)


_WEB_ADDRESS = re.compile(
    r"(?i:[a-z][a-z0-9+.-]*://|\bwww\.)|(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?!\w|\.\d)"
)
_TEMPLATE_MARKS = re.compile(r"\$\w|\$\{|_{3,}")
_LINT_RULES: tuple[tuple[str, Callable[[str], object]], ...] = (
    ("contains a link", lambda text: _WEB_ADDRESS.search(text) or idna_hosts(text)),
    ("contains an email address or handle", re.compile(r"@\w").search),
    # Eight or more digits in one run (spaces, dots, dashes, brackets allowed between them).
    ("contains a phone number", re.compile(r"\+?\d(?:[\s.()-]*\d){7,}").search),
    ("contains a placeholder bracket", re.compile(r"[{}<>\[\]]").search),
    ("contains a template slot", lambda text: printf_slots(text) or _TEMPLATE_MARKS.search(text)),
    (
        "contains a draft marker",
        re.compile(r"\b(?:TODO|TBD|FIXME|XXX+|PLACEHOLDER)\b|lorem ipsum", re.IGNORECASE).search,
    ),
)


@lru_cache(maxsize=4096)
def text_lint_problems(text: str) -> tuple[str, ...]:
    """Reasons ``text`` cannot be shown to users, in rule order (empty when it is clean)."""

    found: list[str] = []
    if unicodedata.normalize("NFC", text) != text:
        found.append("text is not Unicode NFC")
    # Invisible format characters (zero-width space, soft hyphen, word joiner, direction marks)
    # have no place in a sentence and can split a link so that no rule sees it.
    if any(unicodedata.category(char) == "Cf" for char in text):
        found.append("contains an invisible character")
    # Review r6 of #411: case and width are not ways around a rule. Each rule also reads the
    # NFKC, casefolded text, so "VIDU.COM", full-width letters, "Ban@Vi-Du.Test" or full-width
    # digits are caught by the same rule as their plain lower-case form. The folded text also
    # drops invisible characters and reads the ideographic full stop as a dot (r7).
    folded = "".join(
        char
        for char in unicodedata.normalize("NFKC", text).casefold()
        if unicodedata.category(char) != "Cf"
    ).replace("。", ".")
    found.extend(reason for reason, finds in _LINT_RULES if finds(text) or finds(folded))
    return tuple(found)


@dataclass(frozen=True)
class CopyEntry:
    id: str
    category: str
    text: str
    status: str
    approver: str | None = None
    date: str | None = None
    digest: str | None = None

    def problems(self) -> list[str]:
        found: list[str] = []
        if self.status not in STATUSES:
            found.append(f"{self.id}: status must be pending or approved")
        if not self.text.strip():
            found.append(f"{self.id}: empty text")
        found.extend(f"{self.id}: {reason}" for reason in text_lint_problems(self.text))
        if self.status == "approved":
            if self.approver not in APPROVERS:
                found.append(f"{self.id}: approved entry needs approver codex or owner")
            if not self.date:
                found.append(f"{self.id}: approved entry needs a date")
            if self.digest != copy_digest(self.text):
                found.append(f"{self.id}: digest does not match the text")
            if self.category in OWNER_ONLY_CATEGORIES and self.approver != "owner":
                found.append(f"{self.id}: {self.category} copy can only be approved by the owner")
        return found

    @property
    def servable(self) -> bool:
        return self.status == "approved" and not self.problems()


_REQUIRED_TEXT = ("id", "category", "text", "status")
_OPTIONAL_TEXT = ("approver", "date", "digest")


def _entry(raw: object) -> CopyEntry:
    if not isinstance(raw, dict) or set(raw) - {*_REQUIRED_TEXT, *_OPTIONAL_TEXT}:
        raise ValueError("copy entry must be an object with known fields")
    for key in _REQUIRED_TEXT:
        if not isinstance(raw.get(key), str):
            raise ValueError(f"copy entry field {key} must be a string")
    for key in _OPTIONAL_TEXT:
        if raw.get(key) is not None and not isinstance(raw[key], str):
            raise ValueError(f"copy entry field {key} must be a string or null")
    return CopyEntry(**raw)


def parse_registry(data: object) -> dict[str, CopyEntry]:
    if not isinstance(data, dict) or data.get("version") != REGISTRY_VERSION:
        raise ValueError(f"copy registry must be an object with version {REGISTRY_VERSION}")
    raw_entries = data.get("entries", [])
    if not isinstance(raw_entries, list):
        raise ValueError("copy registry entries must be a list")
    entries: dict[str, CopyEntry] = {}
    for raw in raw_entries:
        entry = _entry(raw)
        if entry.id in entries:
            raise ValueError(f"duplicate copy entry: {entry.id}")
        entries[entry.id] = entry
    return entries


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, CopyEntry]:
    return parse_registry(json.loads(path.read_text(encoding="utf-8")))


def registry_problems(entries: dict[str, CopyEntry]) -> list[str]:
    found = [problem for entry in entries.values() for problem in entry.problems()]
    return [*found, *bundle_problems(entries)]


def approved_pin(entries: dict[str, CopyEntry]) -> str:
    """Hash of the approved entries only; pending entries never reach runtime."""

    approved = sorted(
        (e.id, e.category, e.text, e.approver or "", e.digest or "")
        for e in entries.values()
        if e.status == "approved"
    )
    return sha256(json.dumps(approved, ensure_ascii=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def _runtime_registry() -> dict[str, CopyEntry]:
    try:
        return load_registry(REGISTRY_PATH)
    except (OSError, ValueError, TypeError):
        # Fail closed: an unreadable registry serves the current approved sentences.
        return {}


def approved_texts(prefix: str) -> tuple[str, ...]:
    """Approved sentences whose id starts with ``prefix``, in id order; never pending ones."""

    registry = _runtime_registry()
    return tuple(
        registry[key].text
        for key in sorted(registry)
        if key.startswith(prefix) and registry[key].servable
    )


def approved_ids(prefix: str) -> tuple[str, ...]:
    """Ids of the approved entries that start with ``prefix``, in id order."""

    registry = _runtime_registry()
    return tuple(
        key for key in sorted(registry) if key.startswith(prefix) and registry[key].servable
    )


def copy_text(entry_id: str, fallback: str) -> str:
    """The approved sentence for ``entry_id``, or ``fallback`` (current approved copy)."""

    entry = _runtime_registry().get(entry_id)
    return entry.text if entry is not None and entry.servable else fallback


def approved_copy(entry_id: str) -> str | None:
    """The approved sentence for ``entry_id``, or ``None`` while it is pending or broken.

    For copy that has no current approved sentence to fall back to: the caller shows nothing.
    """

    entry = _runtime_registry().get(entry_id)
    return entry.text if entry is not None and entry.servable else None


# Daily bundles (owner decision 10.11.2026): headline, scene and action written together as
# ``daily.bundle.<situation>.<nn>.<part>`` and served only as a whole.
BUNDLE_PREFIX = "daily.bundle."
BUNDLE_PARTS = ("headline", "scene", "action")


def bundle_problems(entries: dict[str, CopyEntry]) -> list[str]:
    """Every bundle id must be ``daily.bundle.<situation>.<nn>.<part>`` with all three parts."""

    groups: dict[str, set[str]] = {}
    found: list[str] = []
    for key in entries:
        if not key.startswith(BUNDLE_PREFIX):
            continue
        parts = key[len(BUNDLE_PREFIX) :].split(".")
        if len(parts) != 3 or not all(parts) or parts[2] not in BUNDLE_PARTS:
            found.append(f"{key}: bundle id must be daily.bundle.<situation>.<nn>.<part>")
            continue
        groups.setdefault(f"{parts[0]}.{parts[1]}", set()).add(parts[2])
    for bundle, present in sorted(groups.items()):
        missing = [part for part in BUNDLE_PARTS if part not in present]
        if missing:
            found.append(f"daily.bundle.{bundle}: missing {', '.join(missing)}")
    return found


def approved_bundles(situation: str) -> tuple[tuple[str, str, str], ...]:
    """(headline, scene, action) bundles of ``situation`` whose three lines are all approved."""

    registry = _runtime_registry()
    prefix = f"{BUNDLE_PREFIX}{situation}."
    numbers = sorted(
        {key[len(prefix) :].split(".")[0] for key in registry if key.startswith(prefix)}
    )
    bundles: list[tuple[str, str, str]] = []
    for number in numbers:
        found = [registry.get(f"{prefix}{number}.{part}") for part in BUNDLE_PARTS]
        lines = [line for line in found if line is not None and line.servable]
        if len(lines) == len(BUNDLE_PARTS):
            bundles.append((lines[0].text, lines[1].text, lines[2].text))
    return tuple(bundles)
