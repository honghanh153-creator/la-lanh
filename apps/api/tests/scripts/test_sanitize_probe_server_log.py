"""The probe receipt's server-log sanitizer (P07, Codex r51): fixtures, no-log and fail-closed.

Synthetic log lines only, written the way PostgreSQL 17 writes them to stderr with the default
``log_line_prefix`` (``%m [%p] ``) and ``log_min_error_statement = error``.
"""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.sanitize_probe_server_log import SAFE_QUOTED, forbidden, main, run

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "sanitize_probe_server_log.py"
ROW = "6f1c2a9e-3b7d-4e21-9a55-0c4d8e7f1b23"
OTHER_ROW = "0b8e4f6a-91c2-4d3e-8f70-5a6b7c8d9e01"


def _log(probe: Path) -> str:
    p = str(probe)
    t = "2026-10-29 10:00:0{} UTC [4242] "
    return "\n".join(
        [
            t.format(1) + "LOG:  starting PostgreSQL 17.11 on aarch64-apple-darwin23.6.0",
            t.format(1) + 'LOG:  listening on IPv4 address "127.0.0.1", port 55440',
            t.format(1) + f'LOG:  listening on Unix socket "{p}/.s.PGSQL.55440"',
            t.format(1) + f'FATAL:  could not load server certificate file "{p}/server.crt": '
            "No such file or directory",
            t.format(1) + 'LOG:  could not bind IPv4 address "127.0.0.1": Address already in use',
            t.format(1) + "HINT:  Is another postmaster already running on port 55440?",
            t.format(2) + 'FATAL:  password authentication failed for user "lalanh_probe"',
            t.format(2) + 'FATAL:  no pg_hba.conf entry for host "127.0.0.1", user '
            '"lalanh_probe", database "lalanh_probe_journal", no encryption',
            t.format(3)
            + 'ERROR:  duplicate key value violates unique constraint "saved_notes_pkey"',
            t.format(3) + f"DETAIL:  Key (id)=({ROW}) already exists.",
            t.format(3) + "STATEMENT:  INSERT INTO saved_notes (id, guest_id, body)",
            f"\tVALUES ('{ROW}', '{OTHER_ROW}', 'synthetic body')",
            "\tRETURNING saved_notes.id",
            t.format(4) + 'ERROR:  invalid input syntax for type uuid: "notauuid"',
            t.format(4) + 'CONTEXT:  SQL function "probe" statement 1',
            t.format(4) + "LOCATION:  string_to_uuid, uuid.c:126",
            t.format(5) + "ERROR:  canceling statement due to user request",
            t.format(5) + "STATEMENT:  DELETE FROM saved_notes WHERE id = $1 RETURNING id",  # noqa: S608 - log text
            t.format(6) + "LOG:  connection from postgresql://lalanh_probe:hunter2@127.0.0.1/x",
            t.format(6)
            + "LOG:  operator note sslkey=abc123 for probe@example.com in /Users/someone",
            t.format(7) + "LOG:  database system is shut down",
        ]
    )


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path]:
    probe = tmp_path / "probe-run"
    receipts = tmp_path / "receipts"
    probe.mkdir()
    receipts.mkdir()
    return probe, receipts


def test_the_realistic_error_log_keeps_diagnostics_and_drops_sql_rows_urls_and_secrets(
    dirs: tuple[Path, Path],
) -> None:
    probe, receipts = dirs
    (probe / "server.log").write_text(_log(probe), encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"

    code, status = run(probe / "server.log", probe, out)

    assert code == 0, status
    assert status.startswith("sanitized: kept ")
    published = out.read_text(encoding="utf-8")
    for removed in (
        ROW,
        OTHER_ROW,
        "INSERT",
        "VALUES",
        "RETURNING",
        "DELETE FROM",
        "synthetic body",
        "Key (id)",
        "notauuid",
        "postgresql://",
        "hunter2",
        "abc123",
        "probe@example.com",
        "/Users/someone",
        "password",
        str(probe),
    ):
        assert removed not in published, removed
    for diagnostic in (
        "LOG:  starting PostgreSQL 17.11 on aarch64-apple-darwin23.6.0",
        'LOG:  listening on IPv4 address "127.0.0.1", port 55440',
        'LOG:  listening on Unix socket "[P]/.s.PGSQL.55440"',
        'FATAL:  could not load server certificate file "[P]/server.crt": No such file',
        'LOG:  could not bind IPv4 address "127.0.0.1": Address already in use',
        "HINT:  Is another postmaster already running on port 55440?",
        "FATAL:  [line removed: credential wording]",
        'database "lalanh_probe_journal", no encryption',
        "ERROR:  duplicate key value violates unique constraint [value]",
        "ERROR:  invalid input syntax for type uuid: [value]",
        "ERROR:  canceling statement due to user request",
        "LOG:  database system is shut down",
    ):
        assert diagnostic in published, diagnostic
    assert "dropped 7 " in published.splitlines()[0]
    assert forbidden(published, [str(probe)]) == []
    assert stat.S_IMODE(out.stat().st_mode) == 0o600
    assert sorted(p.name for p in receipts.iterdir()) == ["server-log.sanitized.txt"]


def test_the_command_line_runs_standalone_with_an_isolated_interpreter(
    dirs: tuple[Path, Path],
) -> None:
    probe, receipts = dirs
    (probe / "server.log").write_text(_log(probe), encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"
    args = ["--log", str(probe / "server.log"), "--probe-dir", str(probe), "--out", str(out)]

    result = subprocess.run(  # noqa: S603 - fixed interpreter and script, synthetic paths
        [sys.executable, "-I", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("sanitized: kept ")
    assert ROW not in result.stdout + result.stderr
    assert ROW not in out.read_text(encoding="utf-8")


def test_a_missing_log_writes_a_no_log_note(dirs: tuple[Path, Path]) -> None:
    probe, receipts = dirs
    out = receipts / "server-log.sanitized.txt"

    code = main(["--log", str(probe / "server.log"), "--probe-dir", str(probe), "--out", str(out)])

    assert code == 0
    assert out.read_text(encoding="utf-8") == "# No server log: [P]/server.log did not exist.\n"


def test_an_empty_log_says_so(dirs: tuple[Path, Path]) -> None:
    probe, receipts = dirs
    (probe / "server.log").write_text("", encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"

    code, status = run(probe / "server.log", probe, out)

    assert (code, status) == (0, "sanitized: kept 0, dropped 0, replaced 0")
    assert "The log held nothing to keep." in out.read_text(encoding="utf-8")


def test_unsafe_content_left_after_sanitizing_writes_nothing(dirs: tuple[Path, Path]) -> None:
    probe, receipts = dirs
    raw = (
        "2026-10-29 10:00:01 UTC [4242] LOG:  starting PostgreSQL 17.11\n"
        "INSERT INTO saved_notes (body) VALUES (1)\n"
    )
    (probe / "server.log").write_text(raw, encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"

    code, status = run(probe / "server.log", probe, out)

    assert code == 2
    assert status == "refused: unsafe content left after sanitizing (sql)"
    assert list(receipts.iterdir()) == []
    assert (probe / "server.log").read_text(encoding="utf-8") == raw


def test_an_unreadable_log_writes_nothing(dirs: tuple[Path, Path]) -> None:
    probe, receipts = dirs
    (probe / "server.log").mkdir()
    out = receipts / "server-log.sanitized.txt"

    code, status = run(probe / "server.log", probe, out)

    assert code == 2
    assert status.startswith("refused: the log could not be read (")
    assert list(receipts.iterdir()) == []


def test_it_refuses_a_receipt_inside_the_probe_directory(dirs: tuple[Path, Path]) -> None:
    probe, _ = dirs
    (probe / "server.log").write_text(_log(probe), encoding="utf-8")

    code, status = run(probe / "server.log", probe, probe / "receipt" / "log.txt")

    assert code == 2
    assert status == "refused: the receipt directory must be outside the probe directory"
    assert sorted(p.name for p in probe.iterdir()) == ["server.log"]


def test_it_never_overwrites_an_earlier_copy(dirs: tuple[Path, Path]) -> None:
    probe, receipts = dirs
    (probe / "server.log").write_text(_log(probe), encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"
    out.write_text("earlier copy\n", encoding="utf-8")

    code, status = run(probe / "server.log", probe, out)

    assert (code, status) == (2, "refused: the output file already exists")
    assert out.read_text(encoding="utf-8") == "earlier copy\n"


@pytest.mark.parametrize(
    ("text", "name"),
    [
        (f"x {ROW}", "uuid"),
        ("x https://example.test/a", "url"),
        ("x a@b.example", "email"),
        ("x /Users/someone/file", "home directory"),
        ("x Password", "password"),
        ("x\n\tcontinued", "continuation line"),
        ("x DETAIL:  Key (id)=(1)", "dropped entry"),
        ("x " + "A" * 40, "long token"),
        ("x select id from saved_notes", "sql"),
        ("x update guest_sessions set a = 1", "sql"),
    ],
)
def test_the_output_check_names_each_unsafe_class(text: str, name: str) -> None:
    assert name in forbidden(text, [])


def test_the_output_check_finds_the_probe_directory() -> None:
    assert forbidden("x /private/tmp/run/server.log", ["/private/tmp/run"]) == ["probe directory"]


def test_kept_quoted_values_are_identifiers_loopback_or_masked_paths_only() -> None:
    for safe in ("saved_notes_pkey", "public.saved_notes", "127.0.0.1", "[P]/server.crt"):
        assert SAFE_QUOTED.fullmatch(safe)
    for unsafe in ("Hello there", ROW, "/var/folders/x", "a'b", "x-y"):
        assert not SAFE_QUOTED.fullmatch(unsafe)


# ------------------------------------------------- Codex r53: quote shapes and Unicode separators

PREFIX = "2026-10-29 10:00:09 UTC [4242] "
SECRET_VALUE = "synthetic_value"  # noqa: S105 - a fixture value, not a password


def _publish(raw: str, dirs: tuple[Path, Path]) -> tuple[int, str]:
    probe, receipts = dirs
    (probe / "server.log").write_text(raw, encoding="utf-8")
    out = receipts / "server-log.sanitized.txt"
    code, _ = run(probe / "server.log", probe, out)
    return code, out.read_text(encoding="utf-8") if out.exists() else ""


@pytest.mark.parametrize(
    "value",
    [
        f"plain{SECRET_VALUE}",  # control: ordinary quoted value
        f'before"{SECRET_VALUE}"after',  # embedded quotes
        f"before\u2028{SECRET_VALUE}",  # LINE SEPARATOR inside the value
        f"before\u2029{SECRET_VALUE}",  # PARAGRAPH SEPARATOR inside the value
        f'"{SECRET_VALUE}',  # unbalanced
    ],
)
def test_an_error_value_is_removed_whatever_its_quote_shape(
    value: str, dirs: tuple[Path, Path]
) -> None:
    raw = f'{PREFIX}ERROR:  invalid input syntax for type uuid: "{value}"\n'
    code, published = _publish(raw, dirs)
    # Either the whole value is gone from an exit-0 copy, or nothing is written.
    assert SECRET_VALUE not in published
    if code == 0:
        assert "ERROR:  invalid input syntax for type uuid: [value]" in published
        assert forbidden(published, []) == []


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\x85", "\x0b"])
def test_a_separator_outside_quotes_in_a_kept_line_refuses_the_copy(
    separator: str, dirs: tuple[Path, Path]
) -> None:
    raw = f"{PREFIX}LOG:  checkpoint starting{separator}{SECRET_VALUE}\n"
    code, published = _publish(raw, dirs)
    assert code == 2
    assert published == ""


def test_a_run_on_quote_in_a_log_line_is_cut(dirs: tuple[Path, Path]) -> None:
    raw = f'{PREFIX}LOG:  could not open "saved_notes"{SECRET_VALUE}" here\n'
    code, published = _publish(raw, dirs)
    assert code == 0
    assert SECRET_VALUE not in published
    assert "LOG:  could not open [value]" in published


def test_crlf_logs_split_on_physical_lines(dirs: tuple[Path, Path]) -> None:
    raw = (
        f"{PREFIX}LOG:  starting PostgreSQL 17.11\r\n{PREFIX}LOG:  database system is shut down\r\n"
    )
    code, published = _publish(raw, dirs)
    assert code == 0
    assert "LOG:  starting PostgreSQL 17.11" in published
    assert "\r" not in published
