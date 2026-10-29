"""Sanitized copy of the disposable probe cluster's server log, for the receipt (P07, Codex r51).

The receipt must be data-free, so the raw log is never attached. PostgreSQL logs the failing
statement of every ERROR by default (``log_min_error_statement = error``, even with
``log_statement = none``), and DETAIL lines can carry row values. This keeps the start-up
diagnostics and removes the rest:

- STATEMENT, QUERY, DETAIL, CONTEXT and LOCATION entries, and every continuation line (PostgreSQL
  starts the later lines of a multi-line message with a tab), are dropped and only counted;
- in the lines kept, the probe directory, home directories, URLs, e-mail addresses, UUIDs, long
  tokens, ``key=value`` secrets and single-quoted literals are replaced, and so are double-quoted
  values other than plain SQL identifiers, loopback addresses and paths under the probe directory
  (in ERROR entries, which can quote an input value, every double-quoted value is replaced);
- a line that mentions a password keeps only its prefix and level.

The result is checked again before anything is written. If anything forbidden is left, or the
copy cannot be made safely, nothing is written and the exit code is 2: the raw log stays inside the
probe directory (fail closed). A missing log writes a one-line note instead.

    python3 -I apps/api/scripts/sanitize_probe_server_log.py \
        --log "$P/server.log" --probe-dir "$P" --out "$R/server-log.sanitized.txt"

Exit codes: 0 sanitized copy or "no log" note written; 2 refused, nothing written. The one status
line on stdout never contains log content. Standard library only, Python 3.9 or newer, so it runs
with the system ``python3 -I`` outside the API environment.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

LEVEL = (
    r"DEBUG[1-5]|INFO|NOTICE|WARNING|ERROR|LOG|FATAL|PANIC|"
    r"DETAIL|HINT|QUERY|CONTEXT|LOCATION|STATEMENT"
)
ENTRY = re.compile(rf"^(?P<head>.*?\b(?P<level>{LEVEL}):  )(?P<message>.*)$")
DROPPED_LEVELS = frozenset({"STATEMENT", "QUERY", "DETAIL", "CONTEXT", "LOCATION"})
DROPPED_ENTRY = re.compile(r"\b(?:STATEMENT|QUERY|DETAIL|CONTEXT|LOCATION):  ")
CREDENTIAL_LINE = "[line removed: credential wording]"

HOME = re.compile(r"/(Users|home)/[^/\s\"']+")
URL = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://\S+")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
UUID = re.compile(r"\b[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}\b")
SECRET = re.compile(r"(?i)\b(\w*(?:secret|token|key|passwd|pwd))\s*[=:]\s*\S+")
SINGLE_QUOTED = re.compile(r"'[^']*'")
DOUBLE_QUOTED = re.compile(r'"([^"]*)"')
SAFE_QUOTED = re.compile(
    r"[a-z_][a-z0-9_$]{0,62}(?:\.[a-z_][a-z0-9_$]{0,62})?"
    r"|127\.0\.0\.1|::1|localhost|0\.0\.0\.0"
    r"|\[P\](?:/[A-Za-z0-9_.-]+)*"
)
TOKEN = re.compile(r"(?<![\w/\[])[A-Za-z0-9+_-]{32,}={0,2}")

FORBIDDEN = (
    ("uuid", UUID),
    ("url", URL),
    ("email", EMAIL),
    ("home directory", re.compile(r"/(?:Users|home)/(?!\[user\])")),
    ("password", re.compile(r"(?i)passw")),
    ("continuation line", re.compile(r"(?m)^[ \t]")),
    ("dropped entry", DROPPED_ENTRY),
    ("long token", TOKEN),
    (
        "sql",
        re.compile(
            r"(?i)\b(?:insert\s+into|delete\s+from|update\s+\w+\s+set|select\s+\S.*\s+from"
            r"|values\s*\(|(?:create|alter|drop)\s+(?:table|role|database|index|user))\b"
        ),
    ),
)


def scrub(line: str, masks: list[str], *, quote_identifiers: bool = True) -> tuple[str, int]:
    """The line with every unsafe value replaced, and how many values were replaced."""

    replaced = 0
    for mask in masks:
        replaced += line.count(mask)
        line = line.replace(mask, "[P]")

    def count(pattern: re.Pattern[str], replacement: str, text: str) -> str:
        nonlocal replaced
        text, n = pattern.subn(replacement, text)
        replaced += n
        return text

    line = count(HOME, r"/\1/[user]", line)
    line = count(URL, "[url]", line)
    line = count(EMAIL, "[email]", line)
    line = count(UUID, "[uuid]", line)
    line = count(SECRET, r"\1=[redacted]", line)
    line = count(SINGLE_QUOTED, "'[value]'", line)

    def quoted(match: re.Match[str]) -> str:
        nonlocal replaced
        if quote_identifiers and SAFE_QUOTED.fullmatch(match.group(1)):
            return match.group(0)
        replaced += 1
        return '"[value]"'

    line = DOUBLE_QUOTED.sub(quoted, line)
    return count(TOKEN, "[token]", line), replaced


def forbidden(text: str, masks: list[str]) -> list[str]:
    """Names of the classes of unsafe content still present; empty means safe to keep."""

    found = [name for name, pattern in FORBIDDEN if pattern.search(text)]
    if any(mask in text for mask in masks):
        found.append("probe directory")
    return found


def sanitize(raw: str, masks: list[str]) -> tuple[list[str], int, int]:
    """Kept lines, the number of dropped lines and the number of replaced values."""

    kept: list[str] = []
    dropped = replaced = 0
    in_dropped_entry = False
    for line in raw.splitlines():
        if not line.strip():
            continue
        entry = ENTRY.match(line)
        level = entry.group("level") if entry else None
        if entry is None and (line[:1] in (" ", "\t") or in_dropped_entry):
            dropped += 1
            continue
        if entry is not None:
            in_dropped_entry = level in DROPPED_LEVELS
            if in_dropped_entry:
                dropped += 1
                continue
        if re.search(r"(?i)passw", line):
            head, n = scrub(entry.group("head"), masks) if entry else ("", 0)
            kept.append(head + CREDENTIAL_LINE)
            replaced += n + 1
            continue
        clean, n = scrub(line, masks, quote_identifiers=level != "ERROR")
        kept.append(clean)
        replaced += n
    return kept, dropped, replaced


def _write_new(out: Path, text: str) -> None:
    """Write ``text`` to ``out`` (mode 600) through a temporary file; never overwrite."""

    temporary = out.with_name(f".{out.name}.partial")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.link(temporary, out)  # fails if ``out`` already exists
    finally:
        temporary.unlink(missing_ok=True)


def run(log: Path, probe_dir: Path, out: Path) -> tuple[int, str]:
    masks = sorted({str(probe_dir), str(probe_dir.resolve())}, key=len, reverse=True)
    out_dir = out.parent.resolve()
    probe = probe_dir.resolve()
    if out_dir == probe or probe in out_dir.parents:
        return 2, "refused: the receipt directory must be outside the probe directory"
    if out.exists():
        return 2, "refused: the output file already exists"
    if not log.exists():
        note = f"# No server log: {log} did not exist.\n"
        text, _ = scrub(note, masks)
        status = "no-log"
    else:
        try:
            raw = log.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            return 2, f"refused: the log could not be read ({error.__class__.__name__})"
        kept, dropped, replaced = sanitize(raw, masks)
        header = (
            "# Sanitized probe server log (apps/api/scripts/sanitize_probe_server_log.py). "
            f"Kept {len(kept)} lines; dropped {dropped} (statement, query, detail, context, "
            f"location and continuation lines); replaced {replaced} values."
        )
        if not kept:
            header += " The log held nothing to keep."
        text = "\n".join([header, *kept]) + "\n"
        status = f"sanitized: kept {len(kept)}, dropped {dropped}, replaced {replaced}"
    leftovers = forbidden(text, masks)
    if leftovers:
        return 2, "refused: unsafe content left after sanitizing (" + ", ".join(leftovers) + ")"
    try:
        _write_new(out, text)
    except OSError as error:
        return 2, f"refused: the copy could not be written ({error.__class__.__name__})"
    return 0, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--probe-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    code, status = run(args.log, args.probe_dir, args.out)
    print(status)
    return code


if __name__ == "__main__":
    sys.exit(main())
